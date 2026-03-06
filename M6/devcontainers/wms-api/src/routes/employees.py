from flask import Blueprint, jsonify, request
from application import logger
from sqlalchemy import text
from database import db_engine

employees_bp = Blueprint('employees_bp', __name__)

@employees_bp.route('/', methods=['GET'])
def get_employees():
    query = text('''
        SELECT
            p.party_id AS employee_id,
            p.name AS employee_name,
            p.created_at AS hire_date,
            STRING_AGG(r.name, ', ') AS roles,
            (
                SELECT json_agg(json_build_object('type', pc.type, 'details', pc.details))
                FROM party_contact pc
                WHERE pc.party_id = p.party_id
            ) AS contacts
        FROM
            party p
        JOIN
            party_role pr ON p.party_id = pr.party_id
        JOIN
            role r ON pr.role_id = r.role_id
        WHERE
            p.data->>'type' = 'employee'
        GROUP BY
            p.party_id, p.name, p.created_at
        ORDER BY
            p.name;
    ''')
    with db_engine.connect() as conn:
        result = conn.execute(query)
        employees = []
        for row in result.mappings():
            emp_dict = dict(row)
            # Default empty list if contacts is None
            contacts = emp_dict.get('contacts') or []
            emp_dict['contacts'] = contacts
            
            # extract email and phone for backward compatibility
            email = next((c['details'] for c in contacts if c['type'] == 'EMAIL'), None)
            phone = next((c['details'] for c in contacts if c['type'] == 'PHONE'), None)
            
            emp_dict['email'] = email
            emp_dict['phone'] = phone
            
            employees.append(emp_dict)

    logger.info(f"Fetched {len(employees)} employees")
    return jsonify(employees)

@employees_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    query = text('''
        SELECT
            p.party_id AS employee_id,
            p.name AS employee_name,
            p.created_at AS hire_date,
            STRING_AGG(r.name, ', ') AS roles,
            (
                SELECT json_agg(json_build_object('type', pc.type, 'details', pc.details))
                FROM party_contact pc
                WHERE pc.party_id = p.party_id
            ) AS contacts
        FROM
            party p
        JOIN
            party_role pr ON p.party_id = pr.party_id
        JOIN
            role r ON pr.role_id = r.role_id
        WHERE
            p.data->>'type' = 'employee'
            AND p.party_id = :employee_id
        GROUP BY
            p.party_id, p.name, p.created_at
        ORDER BY
            p.name;
    ''')
    with db_engine.connect() as conn:
        result = conn.execute(query, {'employee_id': employee_id})
        row = result.mappings().first()
        
        if not row:
            return jsonify({'error': f'Employee id {employee_id} not found'}), 404
            
        employee = dict(row)
        # Default empty list if contacts is None
        contacts = employee.get('contacts') or []
        employee['contacts'] = contacts

        # extract email and phone for backward compatibility
        email = next((c['details'] for c in contacts if c['type'] == 'EMAIL'), None)
        phone = next((c['details'] for c in contacts if c['type'] == 'PHONE'), None)
        
        employee['email'] = email
        employee['phone'] = phone

    logger.info(f"Fetched employee {employee_id}")
    return jsonify(employee)

