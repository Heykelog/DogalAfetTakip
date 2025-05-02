import pandas as pd
from app.models.employee import Employee

class ExcelImporter:
    @staticmethod
    def import_employees(file_path):
        """Import employees from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check required columns
            required_columns = ['name', 'email', 'phone', 'city', 'department']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f"Missing required columns: {', '.join(missing_columns)}"
                }
                
            # Process each row
            success_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if employee with same email already exists
                    existing_employees = Employee.search(query=row['email'])
                    
                    if existing_employees:
                        errors.append(f"Row {index+2}: Employee with email {row['email']} already exists.")
                        continue
                        
                    # Prepare employee data
                    employee_data = {
                        'name': row['name'],
                        'email': row['email'],
                        'phone': str(row['phone']),
                        'city': row['city'],
                        'department': row['department']
                    }
                    
                    # Add optional fields if present
                    optional_fields = ['position', 'address', 'telegram_id', 'emergency_contact']
                    for field in optional_fields:
                        if field in df.columns and not pd.isna(row[field]):
                            employee_data[field] = row[field]
                    
                    # Create employee
                    Employee.create(employee_data)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index+2}: {str(e)}")
            
            return {
                'success': True,
                'total_processed': len(df),
                'success_count': success_count,
                'error_count': len(errors),
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            } 