# Modulio Hotel Core - Odoo 18

## Overview

Modulio Hotel Core is a comprehensive hotel management module for Odoo 18 that provides the foundation for hotel operations including room management, housekeeping, maintenance, and analytics.

## Key Features

### Single State Room Management System

The module uses a **single state system** for room status management, replacing the previous dual state approach. This provides a more streamlined and intuitive workflow for hotel operations.

#### Room States

1. **Clean** - Room is clean and ready for guests
2. **Dirty** - Room needs cleaning
3. **Make Up Room** - Currently being cleaned by housekeeping
4. **Inspected** - Cleaned and inspected, ready for final approval
5. **Out of Service** - Temporary maintenance (light repairs)
6. **Out of Order** - Long-term maintenance (major repairs)
7. **House Use** - Assigned to staff accommodation

#### Status Transitions

The system supports the following status transitions:

**Front Office Operations:**
- `clean/inspected` → `house_use` (Assign House Use)
- `house_use` → `dirty` (Staff Checkout)

**Housekeeping Operations:**
- `dirty` → `make_up_room` (Start Cleaning)
- `make_up_room` → `inspected` (Finish Cleaning)
- `inspected` → `clean` (Final Inspection)

**Maintenance Operations:**
- `clean/dirty` → `out_of_service` (Light Maintenance)
- `clean/dirty` → `out_of_order` (Heavy Maintenance)
- `out_of_service/out_of_order` → `dirty` (Complete Maintenance)

### Core Models

#### Hotel Room (`hotel.room`)
- Single state field with 7 possible values
- Action methods for each status transition
- Integration with housekeeping and maintenance workflows
- Room blocking and availability management

#### Room Status History (`hotel.room.status.history`)
- Tracks all status changes with timestamps
- Supports different change types (FO, HK, MT, System)
- Maintains audit trail for compliance

#### Room Blocking (`hotel.room.blocking`)
- Manages room availability for maintenance and events
- Integrates with single state system
- Supports different blocking types

### Dashboard and Analytics

#### Hotel Dashboard
- Real-time KPI display for all room states
- Filtering by room status, type, and floor
- Visual status indicators with color coding
- Room availability overview

#### Analytics Service
- Centralized analytics data provider
- Room metrics based on single state system
- Performance tracking and reporting

### Views and UI

#### Room Management Views
- **List View**: Shows room number, floor, type, and current state
- **Form View**: Action buttons for status transitions based on current state
- **Kanban View**: Visual room status cards with color coding
- **Calendar View**: Room availability calendar with state-based coloring
- **Search View**: Filter by room status, type, floor, and maintenance

#### Dashboard Views
- **KPI Cards**: Display counts for each room state
- **Room Types Summary**: Availability by room type
- **Rooms Table**: Detailed room status overview

### Security

The module uses group-based access control:
- **Hotel User**: Basic hotel operations access
- **Hotel Manager**: Full hotel management access

### Installation

1. Install the module in Odoo 18
2. Configure hotel settings
3. Create room types and floors
4. Set up rooms with initial states

### Configuration

#### Room Status Configuration
- Default room state: `clean`
- State transitions are enforced by business rules
- Maintenance integration for out-of-service states

#### Dashboard Configuration
- KPI refresh intervals
- Filter persistence
- Color coding for different states

### Usage

#### Front Office
- Assign rooms to house use for staff accommodation
- Check out staff from house use rooms
- Monitor room availability and status

#### Housekeeping
- Start cleaning dirty rooms
- Complete cleaning and mark as inspected
- Perform final inspection to mark as clean

#### Maintenance
- Put rooms under light maintenance (out of service)
- Put rooms under heavy maintenance (out of order)
- Complete maintenance and return to dirty state

### Technical Details

#### Dependencies
- `base` - Core Odoo functionality
- `mail` - Chatter and activity management

#### Python Version
- Compatible with Python 3.12+

#### Database
- PostgreSQL 16+

### Migration from Dual State

The module has been migrated from a dual state system (occupancy_state + housekeeping_state) to a single state system. This provides:

1. **Simplified Workflow**: Single field to track room status
2. **Better Integration**: Unified status for all hotel operations
3. **Improved Performance**: Reduced complexity in queries and views
4. **Enhanced User Experience**: Clearer status indicators and transitions

### Support

For support and questions, please contact the Modulio development team.

### License

This module is licensed under LGPL-3.
