# Hotel Core Module - Modulio

## Overview
Hotel Core adalah modul **fondasi dasar** untuk sistem manajemen hotel di Odoo 18. Sebagai modul core, ia menyediakan struktur fundamental yang diperlukan oleh modul-modul hotel lainnya seperti Front Office dan Housekeeping.

## Key Features

### 1. Room Types Management (Manajemen Tipe Kamar)
- **Model**: `hotel.room.type`
- **Fitur**:
  - Nama dan kode tipe kamar (Standard, Deluxe, Suite)
  - Deskripsi dan fasilitas kamar
  - Kapasitas maksimal tamu (Max Occupancy)
  - Ukuran kamar dalam meter persegi
  - Harga dasar dan mata uang
  - Status aktif/non-aktif
  - Urutan tampilan (sequence)
  - Validasi kode unik dan nama unik

### 2. Room Management (Manajemen Kamar)
- **Model**: `hotel.room`
- **Fitur**:
  - Nomor kamar dan lantai dengan validasi unik per lantai
  - Tipe kamar yang terkait
  - Deskripsi tambahan kamar
  - Catatan maintenance
  - Status tracking dengan timestamp dan alasan perubahan

### 3. Room Status Machine (Mesin Status Kamar)
Implementasi **state machine** yang ketat dengan 6 status:
- **Vacant Ready** → Reserved, Out of Service
- **Reserved** → Occupied, Vacant Ready, Out of Service  
- **Occupied** → Dirty, Out of Service
- **Dirty** → Inspected, Out of Service
- **Inspected** → Vacant Ready, Dirty, Out of Service
- **Out of Service** → Vacant Ready, Dirty, Inspected

### 4. Security & Access Control
- **Hotel User Group**: 
  - Read access untuk room types
  - Read/Write access untuk rooms (tidak bisa create/delete)
- **Hotel Manager Group**: 
  - Full access ke semua fitur
  - Inherit dari Hotel User group
- **Category**: "Modulio Hotel" untuk pengelompokan

### 5. Chatter Integration (Odoo 18)
- **Message Threading** - Komunikasi internal per room type dan room
- **Activity Management** - Tracking tugas dan follow-up
- **Field Tracking** - Log perubahan field penting secara otomatis
- **History Logging** - Riwayat lengkap semua perubahan data
- Menggunakan `<chatter/>` tag sesuai standar Odoo 18

## Installation

1. Copy modul ke direktori addons Odoo
2. Update aplikasi list
3. Install modul "Hotel Core"

## Dependencies
- **Odoo 18.0** (Python 3.12, PostgreSQL 16)
- **Base module** - Modul dasar Odoo
- **Mail module** - Untuk fitur chatter dan activity tracking

## Usage

### Room Types Configuration
1. Navigate to **Hotel Management > Configuration > Room Types**
2. Create room types (Standard, Deluxe, Suite, dll)
3. Set properties:
   - **Code**: Kode unik (otomatis uppercase)
   - **Max Occupancy**: Jumlah maksimal tamu
   - **Size**: Ukuran kamar dalam m²
   - **Base Price**: Harga dasar
   - **Amenities**: Fasilitas yang tersedia
4. Set sequence untuk urutan tampilan

### Room Management
1. Navigate to **Hotel Management > Rooms**
2. Create rooms dengan:
   - **Room Number**: Nomor kamar (unik per lantai)
   - **Floor**: Lantai kamar
   - **Room Type**: Pilih tipe kamar
   - **Description**: Deskripsi tambahan
3. Manage room status melalui status buttons

### Status Management
- **Status Buttons**: Gunakan button di form view untuk mengubah status
- **Validation**: Transisi status divalidasi secara ketat
- **Tracking**: Semua perubahan di-track dengan timestamp dan alasan
- **Maintenance**: Flag maintenance required untuk kamar yang perlu perbaikan

### Chatter & Communication
- **Messages**: Kirim pesan internal per room type atau room
- **Activities**: Buat tugas dan follow-up untuk maintenance
- **Field Tracking**: Semua perubahan field penting akan di-log otomatis
- **History**: Lihat riwayat lengkap perubahan data

## Technical Details

### Models
- **`hotel.room.type`** - Room type definitions
  - Fields: name, code, description, max_occupancy, size_sqm, base_price, amenities
  - Constraints: code_unique, name_unique
  - Methods: action_view_rooms()
- **`hotel.room`** - Individual room records
  - Fields: room_number, floor, room_type_id, status, maintenance_required
  - Constraints: room_number_floor_unique
  - Methods: action_change_status(), status transition methods

### Security
- **Access Rights** berdasarkan user groups
- **Hotel User**: Read access untuk room types, read/write untuk rooms
- **Hotel Manager**: Full access untuk semua models
- **Multi-company Support**: Setiap record terkait dengan company

### Views & UI
- **Tree, Form, Kanban** views untuk room types dan rooms
- **Status-based color coding** untuk visual status management
- **Interactive status buttons** untuk perubahan status
- **Smart buttons** untuk navigasi antar relasi
- **Chatter integration** dengan `<chatter/>` tag Odoo 18

### Data Validation
- **Room Type**: Kode dan nama harus unik
- **Room**: Nomor kamar harus unik per lantai
- **Status Transitions**: Validasi ketat untuk perubahan status
- **Multi-company**: Data terisolasi per perusahaan

### Performance Features
- **Batch Operations**: Menggunakan `@api.model_create_multi`
- **Computed Fields**: Room count dengan `@api.depends`
- **Indexing**: Field penting di-index untuk performa query
- **Related Fields**: Store=True untuk field yang sering diakses

## Integration & Dependencies

### Prerequisites
Modul ini merupakan **fondasi wajib** untuk:
- **Front Office module** - Sistem reservasi dan check-in/out
- **Housekeeping module** - Manajemen cleaning dan maintenance
- **Reservation module** - Sistem booking dan pricing
- **Billing module** - Penagihan berdasarkan room types

### Data Structure Provided
- **Room Types** untuk sistem reservasi dan pricing
- **Room Status** untuk housekeeping dan front office
- **Security Groups** untuk kontrol akses
- **Data Structure** yang konsisten untuk modul hotel lainnya

### Version Compatibility
- **Odoo 18.0** dengan Python 3.12
- **PostgreSQL 16** untuk database
- **OWL 2.0** untuk frontend components
- **Chatter Odoo 18** dengan `<chatter/>` tag

## Development Notes

### Code Quality
- Menggunakan **type hinting** Python 3.12
- **Docstring** untuk semua method penting
- **SQL Constraints** untuk validasi database
- **Field tracking** untuk audit trail

### Best Practices
- **Multi-company aware** - Semua model terkait company
- **Batch operations** - Optimasi untuk create multiple records
- **Status machine** - Implementasi state pattern yang ketat
- **Security first** - Access control yang granular

## Menu Structure

```
Hotel Management
├── Dashboard (menampilkan kamar)
├── Rooms (manajemen kamar)
└── Configuration
    └── Room Types (konfigurasi tipe kamar)
```

## Status Transition Rules

| From Status | To Status | Description |
|-------------|-----------|-------------|
| Vacant Ready | Reserved, Out of Service | Room can be reserved or taken out of service |
| Reserved | Occupied, Vacant Ready, Out of Service | Guest can check-in, cancel reservation, or room goes out of service |
| Occupied | Dirty, Out of Service | Guest checks out, room needs cleaning |
| Dirty | Inspected, Out of Service | Room cleaned and inspected, or taken out of service |
| Inspected | Vacant Ready, Dirty, Out of Service | Room ready for guests, needs re-cleaning, or out of service |
| Out of Service | Vacant Ready, Dirty, Inspected | Room can be brought back to service from any state |

## License
LGPL-3

## Author
Modulio - https://www.modulio.id

## Version
18.0.1.0.2
