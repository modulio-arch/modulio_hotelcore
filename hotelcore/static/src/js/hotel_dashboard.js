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
            kpi: { total: 0, available: 0, occupied: 0, reserved: 0, dirty: 0, clean: 0, inspected: 0, oos: 0 },
            roomTypes: [],
            rooms: [],
            filters: { room_type_id: false, floor: false, start_date: false, end_date: false, occupancy_state: "", housekeeping_state: "" },
            roomTypeOptions: [],
            lastUpdated: null,
            totalAvailabilityRate: 0,
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
            const ctx = this.state.filters;
            
            // Fetch KPI summary per occupancy_state and housekeeping_state
            const total = await this.orm.searchCount("hotel.room", []);
            const available = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "available"]]);
            const occupied = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "occupied"]]);
            const reserved = await this.orm.searchCount("hotel.room", [["occupancy_state", "=", "reserved"]]);
            const oos = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "out_of_service"]]);
            const dirty = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "dirty"]]);
            const clean = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "clean"]]);
            const inspected = await this.orm.searchCount("hotel.room", [["housekeeping_state", "=", "inspected"]]);

            // Check if component is still mounted before updating state
            if (this.state) {
                this.state.kpi = { total, available, occupied, reserved, dirty, clean, inspected, oos };
            }

            // Fetch room types summary from model method
            const summary = await this.orm.call("hotel.room.type", "get_room_type_availability_summary", [ctx.start_date || false, ctx.end_date || false]);
            if (this.state) {
                this.state.roomTypes = summary.room_types || [];
                this.state.totalAvailabilityRate = summary.total_availability_rate || 0;
            }

            // load room type options
            const rt = await this.orm.searchRead("hotel.room.type", [], ["name"], { limit: 200, order: "sequence,name" });
            if (this.state) {
                this.state.roomTypeOptions = rt.map((r) => ({ id: r.id, name: r.name }));
            }

            // Fetch rooms (limited)
            const domain = [];
            if (ctx.room_type_id) domain.push(["room_type_id", "=", ctx.room_type_id]);
            if (ctx.floor) domain.push(["floor", "=", ctx.floor]);
            if (ctx.occupancy_state) domain.push(["occupancy_state", "=", ctx.occupancy_state]);
            if (ctx.housekeeping_state) domain.push(["housekeeping_state", "=", ctx.housekeeping_state]);
            
            console.log("Room filter domain:", domain);
            console.log("Applied filters:", ctx);
            
            const rooms = await this.orm.searchRead("hotel.room", domain, ["room_number", "floor", "room_type_id", "occupancy_state", "housekeeping_state", "maintenance_required", "blocking_count", "blocking_ids"], { limit: 40 });
            
            // Get blocking details for rooms that have blockings
            for (let room of rooms) {
                if (room.blocking_count > 0) {
                    const blockings = await this.orm.searchRead("hotel.room.blocking", 
                        [["room_id", "=", room.id], ["status", "in", ["planned", "active"]]], 
                        ["blocking_type", "name", "status"]
                    );
                    room.blocking_details = blockings;
                }
            }
            if (this.state) {
                this.state.rooms = rooms;
                this.state.loading = false;
                this.state.lastUpdated = new Date().toLocaleTimeString();
                console.log("Dashboard data updated successfully", {
                    kpi: this.state.kpi,
                    roomsCount: this.state.rooms.length,
                    lastUpdated: this.state.lastUpdated
                });
            }
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            if (this.state) {
                this.state.loading = false;
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


