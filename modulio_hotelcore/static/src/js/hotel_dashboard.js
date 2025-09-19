/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillUnmount, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class HotelDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.actionService = useService("action");
        this.state = useState({
            loading: true,
            kpi: { total: 0, available: 0, occupied: 0, reserved: 0, dirty: 0, inspected: 0, clean: 0, oos: 0 },
            roomTypes: [],
            rooms: [],
            filters: { room_type_id: false, floor: false, start_date: false, end_date: false, occupancy_state: false, housekeeping_state: false },
            roomTypeOptions: [],
            lastUpdated: null,
        });

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            // No auto-refresh, only manual refresh via button
        });

        onWillUnmount(() => {
            // Cleanup any pending operations
            this.state.loading = false;
        });
    }

    async loadData() {
        try {
            console.log("Loading dashboard data...");
            this.state.loading = true;
            
        // Simple KPI counts - no complex methods
        const total = await this.orm.searchCount("hotel.room", []);
        const available = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "available"]]);
        const occupied = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "occupied"]]);
        const reserved = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "reserved"]]);
        const dirty = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "dirty"]]);
        const inspected = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "inspected"]]);
        const clean = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "clean"]]);
        const oos = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "out_of_service"]]);

            if (this.state) {
                this.state.kpi = { total, available, occupied, reserved, dirty, inspected, clean, oos };
            }

            // Simple room types list - no complex methods
            const roomTypes = await this.orm.searchRead("hotel.room.type", [], ["name", "code", "room_count"], { limit: 50 });
            if (this.state) {
                this.state.roomTypes = roomTypes.map(rt => ({
                    room_type_id: rt.id,
                    name: rt.name,
                    code: rt.code,
                    total_rooms: rt.room_count,
                    available_rooms: 0, // Will calculate later if needed
                    availability_rate: 0
                }));
                this.state.roomTypeOptions = roomTypes.map((r) => ({ id: r.id, name: r.name }));
            }

            // Simple rooms list - no complex methods
            const rooms = await this.orm.searchRead("hotel.room", [], ["room_number", "floor", "room_type_id", "occupancy_state", "housekeeping_state", "maintenance_required"], { limit: 50 });
            
            if (this.state) {
                this.state.rooms = rooms;
                this.state.loading = false;
                this.state.lastUpdated = new Date().toLocaleTimeString();
                console.log("Dashboard data loaded successfully", {
                    kpi: this.state.kpi,
                    roomsCount: this.state.rooms.length,
                    lastUpdated: this.state.lastUpdated
                });
            }
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            if (this.state) {
                this.state.loading = false;
                this.state.kpi = { total: 0, available: 0, occupied: 0, reserved: 0, dirty: 0, inspected: 0, clean: 0, oos: 0 };
                this.state.roomTypes = [];
                this.state.rooms = [];
            }
        }
    }

    async applyFilters() {
        console.log("Applying filters...");
        
        // Get values from form elements using document.querySelector
        const occupancyEl = document.querySelector('select[name="occupancy_state"]');
        const housekeepingEl = document.querySelector('select[name="housekeeping_state"]');
        const roomTypeEl = document.querySelector('select[name="room_type_id"]');
        const floorEl = document.querySelector('input[name="floor"]');
        const startDateEl = document.querySelector('input[name="start_date"]');
        const endDateEl = document.querySelector('input[name="end_date"]');
        
        const occupancyValue = occupancyEl?.value || "";
        const housekeepingValue = housekeepingEl?.value || "";
        const roomTypeValue = roomTypeEl?.value || "";
        const floorValue = floorEl?.value || "";
        const startDateValue = startDateEl?.value || "";
        const endDateValue = endDateEl?.value || "";
        
        console.log("Raw form values:", {
            occupancy: occupancyValue,
            housekeeping: housekeepingValue,
            roomType: roomTypeValue,
            floor: floorValue,
            startDate: startDateValue,
            endDate: endDateValue
        });
        
        console.log("Form elements found:", {
            occupancyEl: !!occupancyEl,
            housekeepingEl: !!housekeepingEl,
            roomTypeEl: !!roomTypeEl,
            floorEl: !!floorEl,
            startDateEl: !!startDateEl,
            endDateEl: !!endDateEl
        });
        
        // Update filters state
        this.state.filters = {
            occupancy_state: occupancyValue || false,
            housekeeping_state: housekeepingValue || false,
            room_type_id: roomTypeValue ? parseInt(roomTypeValue) : false,
            floor: floorValue ? parseInt(floorValue) : false,
            start_date: startDateValue || false,
            end_date: endDateValue || false,
        };
        
        console.log("Filters applied:", this.state.filters);
        await this.loadData();
    }

    async clearFilters() {
        console.log("Clearing filters...");
        
        // Reset form elements using document.querySelector
        const occupancyEl = document.querySelector('select[name="occupancy_state"]');
        const housekeepingEl = document.querySelector('select[name="housekeeping_state"]');
        const roomTypeEl = document.querySelector('select[name="room_type_id"]');
        const floorEl = document.querySelector('input[name="floor"]');
        const startDateEl = document.querySelector('input[name="start_date"]');
        const endDateEl = document.querySelector('input[name="end_date"]');
        
        if (occupancyEl) occupancyEl.value = "";
        if (housekeepingEl) housekeepingEl.value = "";
        if (roomTypeEl) roomTypeEl.value = "";
        if (floorEl) floorEl.value = "";
        if (startDateEl) startDateEl.value = "";
        if (endDateEl) endDateEl.value = "";
        
        // Reset filters state
        this.state.filters = {
            room_type_id: false,
            floor: false,
            start_date: false,
            end_date: false,
            occupancy_state: false,
            housekeeping_state: false,
        };
        
        console.log("Filters cleared");
        await this.loadData();
    }

    openRoom(recId) {
        // Simple navigation without action service for now
        window.location.href = `/web#id=${recId}&model=hotel.room&view_type=form`;
    }

    async refreshData() {
        console.log("Manual refresh triggered");
        try {
            this.state.loading = true;
            await this.loadData();
            console.log("Refresh completed");
        } catch (error) {
            console.error("Refresh error:", error);
        }
    }
}

HotelDashboard.template = "modulio_hotelcore.HotelDashboard";

registry.category("actions").add("hotel_dashboard", HotelDashboard);

export default HotelDashboard;


