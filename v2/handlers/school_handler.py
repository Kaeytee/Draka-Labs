import json

def not_implemented(request):
    request._set_headers(501)
    request.wfile.write(json.dumps({"error": "Not implemented"}).encode('utf-8'))

def handle_list_schools(request):
    not_implemented(request)
import json
from services.school_services import update_school_grading_system
from utils.auth import require_role

@require_role(['admin'])
def handle_update_grading_system(request, school_id):
    """
    HTTP handler for updating a school's grading system.
    Expects JSON body: { "grading_system": [...] }
    """
    try:
        body = json.loads(request.body)
    except Exception:
        return {
            "status": 400,
            "body": json.dumps({"error": "Invalid JSON body."})
        }
    grading_system = body.get("grading_system")
    if grading_system is None:
        return {
            "status": 400,
            "body": json.dumps({"error": "Missing required field: grading_system"})
        }
    if not isinstance(grading_system, list):
        return {
            "status": 400,
            "body": json.dumps({"error": "grading_system must be a list."})
        }
    # Validate each grading rule
    for rule in grading_system:
        if not (isinstance(rule, dict) and "grade" in rule and "min" in rule and "max" in rule):
            return {
                "status": 400,
                "body": json.dumps({"error": "Each grading rule must be a dict with grade, min, and max."})
            }
    school, error = update_school_grading_system(school_id, grading_system)
    if error:
        return {
            "status": 400,
            "body": json.dumps({"error": error})
        }
    return {
        "status": 200,
        "body": json.dumps({
            "message": "Grading system updated successfully.",
            "school_id": school.id,
            "grading_system": json.loads(school.grading_system)
        })
    }