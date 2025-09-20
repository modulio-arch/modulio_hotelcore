# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Migrate existing room data to include floor_id references"""
    
    # First, create floors if they don't exist
    cr.execute("""
        INSERT INTO hotel_floor (name, floor_number, sequence, active, company_id, create_date, write_date, create_uid, write_uid)
        SELECT 
            CASE 
                WHEN floor_number = 0 THEN 'Ground Floor'
                WHEN floor_number = 1 THEN 'First Floor'
                WHEN floor_number = 2 THEN 'Second Floor'
                WHEN floor_number = 3 THEN 'Third Floor'
                WHEN floor_number = 4 THEN 'Fourth Floor'
                ELSE 'Floor ' || floor_number::text
            END as name,
            floor_number,
            (floor_number + 1) * 10 as sequence,
            true as active,
            company_id,
            NOW() as create_date,
            NOW() as write_date,
            1 as create_uid,
            1 as write_uid
        FROM (
            SELECT DISTINCT floor as floor_number, company_id 
            FROM hotel_room 
            WHERE floor IS NOT NULL
        ) AS distinct_floors
        WHERE NOT EXISTS (
            SELECT 1 FROM hotel_floor hf 
            WHERE hf.floor_number = distinct_floors.floor_number 
            AND hf.company_id = distinct_floors.company_id
        )
    """)
    
    # Update room records to link to floor_id
    cr.execute("""
        UPDATE hotel_room 
        SET floor_id = hf.id
        FROM hotel_floor hf
        WHERE hotel_room.floor = hf.floor_number 
        AND hotel_room.company_id = hf.company_id
        AND hotel_room.floor_id IS NULL
    """)
    
    # Now we can safely set floor_id as required
    # This will be done in the next migration step
