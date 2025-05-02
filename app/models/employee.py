from app.models.database import db
from datetime import datetime
from bson import ObjectId

class Employee:
    COLLECTION = 'employees'
    
    # Status constants
    STATUS_UNKNOWN = 'unknown'
    STATUS_SAFE = 'safe'
    STATUS_TRAPPED = 'trapped'
    STATUS_MEDICAL_HELP = 'medical_help'
    STATUS_SUPPORT_NEEDED = 'support_needed'
    
    # Türkiye bölgeleri
    REGION_MARMARA = 'marmara'
    REGION_AEGEAN = 'aegean'
    REGION_BLACK_SEA = 'black_sea'
    REGION_MEDITERRANEAN = 'mediterranean'
    REGION_CENTRAL_ANATOLIA = 'central_anatolia'
    REGION_EASTERN_ANATOLIA = 'eastern_anatolia'
    REGION_SOUTHEASTERN_ANATOLIA = 'southeastern_anatolia'
    
    # Türkiye bölgeleri ve şehirleri
    REGIONS_AND_CITIES = {
        REGION_MARMARA: ['İstanbul', 'Bursa', 'Kocaeli', 'Sakarya', 'Tekirdağ', 'Edirne', 'Kırklareli', 'Balıkesir', 'Çanakkale', 'Yalova', 'Bilecik'],
        REGION_AEGEAN: ['İzmir', 'Aydın', 'Muğla', 'Manisa', 'Denizli', 'Kütahya', 'Afyonkarahisar', 'Uşak'],
        REGION_BLACK_SEA: ['Samsun', 'Trabzon', 'Rize', 'Ordu', 'Giresun', 'Artvin', 'Gümüşhane', 'Bayburt', 'Bartın', 'Kastamonu', 'Çorum', 'Sinop', 'Amasya', 'Tokat', 'Zonguldak', 'Karabük', 'Düzce', 'Bolu'],
        REGION_MEDITERRANEAN: ['Antalya', 'Mersin', 'Adana', 'Hatay', 'Osmaniye', 'Kahramanmaraş', 'Burdur', 'Isparta'],
        REGION_CENTRAL_ANATOLIA: ['Ankara', 'Konya', 'Kayseri', 'Eskişehir', 'Sivas', 'Kırıkkale', 'Aksaray', 'Niğde', 'Nevşehir', 'Kırşehir', 'Karaman', 'Yozgat'],
        REGION_EASTERN_ANATOLIA: ['Erzurum', 'Malatya', 'Elazığ', 'Van', 'Kars', 'Ağrı', 'Ardahan', 'Iğdır', 'Tunceli', 'Bingöl', 'Erzincan', 'Muş', 'Bitlis', 'Hakkari'],
        REGION_SOUTHEASTERN_ANATOLIA: ['Gaziantep', 'Şanlıurfa', 'Diyarbakır', 'Mardin', 'Batman', 'Siirt', 'Şırnak', 'Adıyaman', 'Kilis']
    }
    
    @staticmethod
    def create(employee_data):
        """Create a new employee record"""
        employee_data['created_at'] = datetime.utcnow()
        employee_data['updated_at'] = datetime.utcnow()
        employee_data['status'] = Employee.STATUS_UNKNOWN
        employee_data['status_history'] = []
        
        # Şehir bilgisi varsa, bölge bilgisini otomatik doldur
        if 'city' in employee_data and employee_data['city']:
            employee_data['region'] = Employee.get_region_for_city(employee_data['city'])
        
        result = db.connect()[Employee.COLLECTION].insert_one(employee_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get(employee_id):
        """Get employee by ID"""
        return db.connect()[Employee.COLLECTION].find_one({'_id': ObjectId(employee_id)})
    
    @staticmethod
    def get_all():
        """Get all employees"""
        return list(db.connect()[Employee.COLLECTION].find())
    
    @staticmethod
    def update(employee_id, update_data):
        """Update employee data"""
        update_data['updated_at'] = datetime.utcnow()
        
        # Şehir bilgisi güncellendiyse, bölge bilgisini de güncelle
        if 'city' in update_data and update_data['city']:
            update_data['region'] = Employee.get_region_for_city(update_data['city'])
        
        return db.connect()[Employee.COLLECTION].update_one(
            {'_id': ObjectId(employee_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def update_status(employee_id, new_status):
        """Update employee status and record in history"""
        current_time = datetime.utcnow()
        
        # Get current employee data
        employee = Employee.get(employee_id)
        
        if employee:
            old_status = employee.get('status', Employee.STATUS_UNKNOWN)
            # Add status change to history
            status_change = {
                'from_status': old_status,
                'to_status': new_status,
                'changed_at': current_time
            }
            
            db.connect()[Employee.COLLECTION].update_one(
                {'_id': ObjectId(employee_id)},
                {
                    '$set': {'status': new_status, 'updated_at': current_time},
                    '$push': {'status_history': status_change}
                }
            )
            return True
        return False
    
    @staticmethod
    def search(query=None, city=None, status=None, region=None):
        """Search employees with various filters"""
        search_filter = {}
        
        if query:
            search_filter['$or'] = [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}},
                {'phone': {'$regex': query, '$options': 'i'}}
            ]
        
        if city:
            search_filter['city'] = city
            
        if status:
            search_filter['status'] = status
            
        if region:
            search_filter['region'] = region
            
        return list(db.connect()[Employee.COLLECTION].find(search_filter))
    
    @staticmethod
    def get_by_city(city):
        """Get all employees in a city"""
        return list(db.connect()[Employee.COLLECTION].find({'city': city}))
        
    @staticmethod
    def get_by_region(region):
        """Get all employees in a region"""
        return list(db.connect()[Employee.COLLECTION].find({'region': region}))
    
    @staticmethod
    def get_by_cities(cities):
        """Get all employees in multiple cities"""
        return list(db.connect()[Employee.COLLECTION].find({'city': {'$in': cities}}))
    
    @staticmethod
    def get_by_regions(regions):
        """Get all employees in multiple regions"""
        return list(db.connect()[Employee.COLLECTION].find({'region': {'$in': regions}}))
    
    @staticmethod
    def delete(employee_id):
        """Delete an employee"""
        return db.connect()[Employee.COLLECTION].delete_one({'_id': ObjectId(employee_id)})
        
    @staticmethod
    def delete_many(employee_ids):
        """Delete multiple employees"""
        object_ids = [ObjectId(id) for id in employee_ids if id]
        if not object_ids:
            return None
            
        result = db.connect()[Employee.COLLECTION].delete_many({'_id': {'$in': object_ids}})
        return result
    
    @staticmethod
    def get_region_for_city(city):
        """Şehir adına göre bölge bilgisini döndürür"""
        for region, cities in Employee.REGIONS_AND_CITIES.items():
            if city in cities:
                return region
        return None
    
    @staticmethod
    def get_all_regions():
        """Tüm bölgelerin listesini döndürür"""
        return list(Employee.REGIONS_AND_CITIES.keys())
    
    @staticmethod
    def get_cities_in_region(region):
        """Belirli bir bölgedeki şehirlerin listesini döndürür"""
        return Employee.REGIONS_AND_CITIES.get(region, [])
        
    @staticmethod
    def update_all_employee_regions():
        """Tüm çalışanların bölge bilgilerini şehirlerine göre günceller"""
        employees = Employee.get_all()
        updated_count = 0
        
        for employee in employees:
            if 'city' in employee and employee['city'] and ('region' not in employee or not employee['region']):
                region = Employee.get_region_for_city(employee['city'])
                if region:
                    Employee.update(str(employee['_id']), {'region': region})
                    updated_count += 1
                    
        return updated_count 