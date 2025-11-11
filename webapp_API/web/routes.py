from flask import request, render_template, render_template_string
import json
import requests
from datetime import datetime
from . import web_bp


@web_bp.route('/')
def index():
    return render_template('landing.html')

@web_bp.route('/map_data', methods=["POST", "GET"])
def map_data():
    return render_template('wwf-index.html')


@web_bp.route("/add-lot", methods=["POST"])
def add_lot():
    feature = json.loads(request.form.get("feature"))
    
    # Extract properties
    properties = feature["properties"]
    lot_number = properties.get("lot", "")
    plan_name = properties.get("plan", "")
    object_id = properties.get("OBJECTID", "")
    
    # Construct lot identifier
    lot_identifier = f"{lot_number}/{plan_name}"
    
    # Generate a unique lot_id using object_id
    lot_id = f"lot-{object_id}"
    
    # Store geometry as string
    geometry_str = json.dumps(feature["geometry"])
    
    # Calculate area if shape_Area exists, otherwise use placeholder
    #area = properties.get("shape_Area", 0)
    area = properties.get("area", 0)
    status = "Titled"  # Default status, modify as needed

    return render_template_string(f'''
    <div id="{lot_id}" class="flex justify-between items-center bg-gray-100 p-2 rounded-md mb-2">
        <div>
            <p id="identifier-display-{lot_id}" class="text-sm font-medium">{lot_identifier}</p>
            <p class="text-xs text-gray-600">{status} - {area:.1f} ha</p>
            <!-- Hidden inputs with unique IDs -->
            <input type="hidden" id="identifier-{lot_id}" name="identifier" value="{lot_identifier}">
            <input type="hidden" id="objectid-{lot_id}" name="objectid" value="{object_id}">
            <input type="hidden" id="geometry-{lot_id}" name="geometry" value='{geometry_str}'>
        </div>
        
        <!-- Dialog trigger button -->
        <button
            onclick="document.getElementById('dialog-{lot_id}').showModal()"
            class="text-red-500 hover:text-red-700">
            <i class="fas fa-trash w-5 h-5"></i>
        </button>

        <!-- Confirmation Dialog -->
        <dialog id="dialog-{lot_id}" class="rounded-lg shadow-lg p-0 backdrop:bg-gray-500/50">
            <div class="p-4 min-w-[300px]">
                <h3 class="text-lg font-semibold mb-2">Confirm Deletion</h3>
                <p class="text-gray-600 mb-4">Are you sure you want to delete this lot?</p>
                
                <div class="flex justify-end gap-2">
                    <button
                        onclick="document.getElementById('dialog-{lot_id}').close()"
                        class="px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-100">
                        Cancel
                    </button>
                    <button
                        hx-post="/remove-lot"
                        hx-vals='{{"lot_id": "{lot_id}"}}'
                        hx-target="#{lot_id}"
                        hx-swap="outerHTML"
                        onclick="document.getElementById('dialog-{lot_id}').close()"
                        class="px-3 py-1.5 bg-red-500 text-white rounded-md hover:bg-red-600">
                        Delete
                    </button>
                </div>
            </div>
        </dialog>
    </div>
    ''')

@web_bp.route("/delete-all", methods=["POST"])
def delete_all():
    print("Removing all")
    return ""  # Clears the list.

@web_bp.route("/remove-lot", methods=["POST"])
def remove_lot():
    print("Removing lot")
    return ""  # The hx-swap="outerHTML" removes the element from the DOM.





@web_bp.route('/report', methods=["POST", "GET"])
def report():
    print("Generating report")
    
    dataset = request.form.get('dataset', 'aus')
    identifiers = request.form.getlist('identifier')
    object_ids = request.form.getlist('objectid')
    geometries = request.form.getlist('geometry')
    
    deforestation_results = []
    no_deforestation_results = []
    if dataset == 'fao':
        expr = "defor=Defqld.fao@(year=2023)\nwwf_summary(defor, resolution, area)"
    else:  # default to aus
        expr = "defor=Defqld.aus@(year=2023)\nwwf_summary(defor, resolution, area)"
    for i in range(len(object_ids)):
        wcs_payload = {
            "feature": {
                "type": "Feature",
                "geometry": json.loads(geometries[i])
            },
            "in_crs": "epsg:4326",
            "out_crs": "epsg:3577",
            "resolution": -1,
            "expr": expr,
            "output": "json"
        }
        
        response = requests.post(
            'https://dev-eu.terrak.io/wcs',
            json=wcs_payload
        )
        print("the response is ", response)
        
        if response.status_code == 200:
            data_dict = {
                'identifier': identifiers[i],
                'stats': {}
            }
            
            response_json = response.json()
            
            # First check dfree status
            dfree = None
            for item in response_json['data']:
                if item['index'] == 'dfree':
                    dfree = item['values']
                    break
            
            # Then get all other stats
            for item in response_json['data']:
                if item['index'] in ['area_ha', 'forest_area_ha', 'deforested_2021_area_ha',
                                   'deforested_2022_area_ha', 'deforested_2023_area_ha',
                                   'total_deforested_area_ha', 'deforestation_perc_since_2020']:
                    data_dict['stats'][item['index']] = float(item['values'])
            
            # Add to appropriate list based on dfree status
            if dfree:
                no_deforestation_results.append(data_dict)
            else:
                deforestation_results.append(data_dict)

    return render_template('wwf_report.html', 
                         deforestation_results=deforestation_results,
                         no_deforestation_results=no_deforestation_results, dataset= dataset, now =datetime.now())

@web_bp.route('/self_assessment', methods=["POST", "GET"])
def assessment():
    return render_template('defor_assessment.html')

@web_bp.route('/data')
def data():
    return render_template('data-download.html')
