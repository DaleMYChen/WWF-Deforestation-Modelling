from flask import request, jsonify
import json
import requests
from datetime import datetime
from . import api_bp

@api_bp.route('/report', methods=["POST"])
def api_report():
    """
    API endpoint for generating reports, returns JSON only.
    This route is designed for JavaScript clients.
    """
    print("Generating API report")
    
    dataset = request.json.get('dataset', 'aus')
    lots = request.json.get('lots', [])
    
    # Set up expression based on dataset
    if dataset == 'fao':
        expr = "defor=Defqld.fao@(year=2023)\nwwf_summary(defor, resolution, area)"
    else:  # default to aus
        expr = "defor=Defqld.aus@(year=2023)\nwwf_summary(defor, resolution, area)"
    
    # Process each lot
    deforestation_results = []
    no_deforestation_results = []
    errors = []
    
    for lot in lots:
        try:
            # Validate required fields
            if 'geometry' not in lot or 'identifier' not in lot:
                errors.append(f"Missing required fields for lot {lot.get('id', 'unknown')}")
                continue
                
            wcs_payload = {
                "feature": {
                    "type": "Feature",
                    "geometry": lot['geometry']
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
            
            if response.status_code != 200:
                errors.append(f"API error for lot {lot.get('id', 'unknown')}: {response.status_code}")
                continue
                
            data_dict = {
                'identifier': lot['identifier'],
                'lot_id': lot.get('id', ''),
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
                
        except Exception as e:
            errors.append(f"Error processing lot {lot.get('id', 'unknown')}: {str(e)}")

    # Return JSON response
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'dataset': dataset,
        'deforestation_results': deforestation_results,
        'no_deforestation_results': no_deforestation_results,
        'errors': errors
    })