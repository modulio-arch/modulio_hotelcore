# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelRoomStatusHistory(models.Model):
    _name = 'hotel.room.status.history'
    _description = 'Hotel Room Status History'
    _order = 'change_date desc, id desc'
    _rec_name = 'display_name'

    # Basic Information
    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        index=True,
        ondelete='cascade',
        help='Room that had status change'
    )
    room_number = fields.Char(
        related='room_id.room_number',
        string='Room Number',
        store=True,
        help='Room number for easy reference'
    )
    floor_id = fields.Many2one(
        related='room_id.floor_id',
        string='Floor',
        store=True,
        help='Floor where the room is located'
    )
    room_type_id = fields.Many2one(
        related='room_id.room_type_id',
        string='Room Type',
        store=True,
        help='Type of the room'
    )

    # Status Change Information
    change_type = fields.Selection([
        ('fo', 'Front Office'),
        ('hk', 'Housekeeping'),
        ('mt', 'Maintenance'),
        ('blocking', 'Blocking Status'),
        ('system', 'System'),
        ('other', 'Other'),
    ], string='Change Type', required=True, index=True,
       help='Type of status change')

    # Single State Tracking
    old_state = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('make_up_room', 'Make Up Room'),
        ('inspected', 'Inspected'),
        ('out_of_service', 'Out of Service'),
        ('out_of_order', 'Out of Order'),
        ('house_use', 'House Use'),
    ], string='Previous State', help='Previous room state')

    new_state = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('make_up_room', 'Make Up Room'),
        ('inspected', 'Inspected'),
        ('out_of_service', 'Out of Service'),
        ('out_of_order', 'Out of Order'),
        ('house_use', 'House Use'),
    ], string='New State', help='New room state')

    old_maintenance_required = fields.Boolean(
        string='Previous Maintenance Required',
        help='Previous maintenance required status'
    )

    new_maintenance_required = fields.Boolean(
        string='New Maintenance Required',
        help='New maintenance required status'
    )

    # Change Details
    change_reason = fields.Text(
        string='Change Reason',
        help='Reason for the status change'
    )
    change_method = fields.Char(
        string='Change Method',
        help='Method used to change status (e.g., action_check_in, action_housekeeping_clean)'
    )
    change_notes = fields.Text(
        string='Change Notes',
        help='Additional notes about the change'
    )

    # User and Date Information
    changed_by = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User who made the change'
    )
    change_date = fields.Datetime(
        string='Change Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='When the change occurred'
    )
    change_date_date = fields.Date(
        string='Change Date (Date)',
        compute='_compute_change_date_date',
        store=True,
        help='Date part of change date for filtering'
    )

    # System Information
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='room_id.company_id',
        store=True,
        help='Company of the room'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this history record is active'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the history record'
    )
    status_summary = fields.Char(
        string='Status Summary',
        compute='_compute_status_summary',
        store=True,
        help='Summary of the status change'
    )
    has_changes = fields.Boolean(
        string='Has Changes',
        compute='_compute_has_changes',
        store=True,
        help='Whether there are actual changes in this record'
    )

    @api.depends('change_date')
    def _compute_change_date_date(self):
        """Extract date part from change_date for filtering"""
        for record in self:
            if record.change_date:
                record.change_date_date = record.change_date.date()
            else:
                record.change_date_date = False

    @api.depends('room_number', 'change_type', 'change_date')
    def _compute_display_name(self):
        """Compute display name for the history record"""
        for record in self:
            if record.room_number and record.change_type and record.change_date:
                record.display_name = f"{record.room_number} - {record.change_type.title()} - {record.change_date.strftime('%Y-%m-%d %H:%M')}"
            else:
                record.display_name = f"Room Status History - {record.id}"

    @api.depends('old_state', 'new_state', 'old_maintenance_required', 'new_maintenance_required')
    def _compute_status_summary(self):
        """Compute status change summary"""
        for record in self:
            changes = []
            
            if record.old_state != record.new_state:
                changes.append(f"State: {record.old_state or 'N/A'} → {record.new_state or 'N/A'}")
            
            if record.old_maintenance_required != record.new_maintenance_required:
                changes.append(f"Maintenance: {record.old_maintenance_required} → {record.new_maintenance_required}")
            
            record.status_summary = '; '.join(changes) if changes else 'No changes'

    @api.depends('old_state', 'new_state', 'old_maintenance_required', 'new_maintenance_required')
    def _compute_has_changes(self):
        """Check if there are actual changes in this record"""
        for record in self:
            record.has_changes = (
                record.old_state != record.new_state or
                record.old_maintenance_required != record.new_maintenance_required
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate data and set change type"""
        for vals in vals_list:
            # Auto-detect change type if not provided
            if 'change_type' not in vals or not vals['change_type']:
                vals['change_type'] = self._detect_change_type(vals)
            
            # Validate that there are actual changes
            if not self._has_actual_changes(vals):
                raise ValidationError("No actual changes detected. History record not created.")
        
        return super().create(vals_list)

    def _detect_change_type(self, vals):
        """Auto-detect change type based on changed fields"""
        if 'new_state' in vals or 'old_state' in vals:
            return 'state'
        elif 'new_maintenance_required' in vals or 'old_maintenance_required' in vals:
            return 'maintenance'
        else:
            return 'other'

    def _has_actual_changes(self, vals):
        """Check if there are actual changes in the values"""
        return (
            vals.get('old_state') != vals.get('new_state') or
            vals.get('old_maintenance_required') != vals.get('new_maintenance_required')
        )

    @api.model
    def create_status_change(self, room_id, change_type, old_values, new_values, 
                           change_reason='', change_method='', change_notes='', changed_by=None):
        """Create a status change history record"""
        if not changed_by:
            changed_by = self.env.user.id
        
        history_vals = {
            'room_id': room_id,
            'change_type': change_type,
            'old_state': old_values.get('state'),
            'new_state': new_values.get('state'),
            'old_maintenance_required': old_values.get('maintenance_required'),
            'new_maintenance_required': new_values.get('maintenance_required'),
            'change_reason': change_reason,
            'change_method': change_method,
            'change_notes': change_notes,
            'changed_by': changed_by,
            'change_date': fields.Datetime.now(),
        }
        
        return self.create(history_vals)

    @api.model
    def get_room_history(self, room_id, limit=50, change_type=None, date_from=None, date_to=None):
        """Get history for a specific room with optional filters"""
        domain = [('room_id', '=', room_id)]
        
        if change_type:
            domain.append(('change_type', '=', change_type))
        
        if date_from:
            domain.append(('change_date', '>=', date_from))
        
        if date_to:
            domain.append(('change_date', '<=', date_to))
        
        return self.search(domain, limit=limit)

    @api.model
    def get_room_status_timeline(self, room_id, start_date, end_date):
        """Get room status timeline for a specific period"""
        domain = [
            ('room_id', '=', room_id),
            ('change_date', '>=', start_date),
            ('change_date', '<=', end_date),
            ('has_changes', '=', True)
        ]
        
        history = self.search(domain, order='change_date asc')
        
        timeline = []
        for record in history:
            timeline.append({
                'id': record.id,
                'date': record.change_date,
                'change_type': record.change_type,
                'status_summary': record.status_summary,
                'changed_by': record.changed_by.name,
                'change_reason': record.change_reason,
                'change_method': record.change_method,
            })
        
        return timeline

    @api.model
    def get_room_status_summary(self, room_id, days=30):
        """Get room status summary for the last N days"""
        end_date = fields.Datetime.now()
        start_date = end_date - fields.timedelta(days=days)
        
        domain = [
            ('room_id', '=', room_id),
            ('change_date', '>=', start_date),
            ('change_date', '<=', end_date),
            ('has_changes', '=', True)
        ]
        
        history = self.search(domain)
        
        # Count changes by type
        change_counts = {}
        for record in history:
            change_type = record.change_type
            change_counts[change_type] = change_counts.get(change_type, 0) + 1
        
        # Get latest status
        latest_record = history[0] if history else None
        
        return {
            'room_id': room_id,
            'period_days': days,
            'total_changes': len(history),
            'change_counts': change_counts,
            'latest_change': {
                'date': latest_record.change_date if latest_record else None,
                'type': latest_record.change_type if latest_record else None,
                'summary': latest_record.status_summary if latest_record else None,
                'changed_by': latest_record.changed_by.name if latest_record else None,
            } if latest_record else None,
        }

    def action_view_room(self):
        """Action to view the room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room - {self.room_number}',
            'res_model': 'hotel.room',
            'view_mode': 'form',
            'res_id': self.room_id.id,
            'target': 'current',
        }

    _sql_constraints = [
        ('room_change_date_unique', 'UNIQUE(room_id, change_date, change_type)', 
         'Duplicate status change record for the same room, date, and type!'),
    ]
