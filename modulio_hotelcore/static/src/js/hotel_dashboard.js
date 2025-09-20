/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillUnmount, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class HotelDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.actionService = useService("action");
        
        // Initialize state management
        this.initializeState();
        
        // Initialize watchers and computed properties
        this.initializeWatchers();
        
        // Initialize persistence
        this.initializePersistence();

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            // No auto-refresh, only manual refresh via button
        });

        onWillUnmount(() => {
            // Cleanup any pending operations
            this.state.loading = false;
            if (this.filterDebounceTimer) {
                clearTimeout(this.filterDebounceTimer);
            }
            // Save state to localStorage
            this.saveStateToStorage();
        });
    }

    initializeState() {
        // Core state
        this.state = useState({
            // Loading states
            loading: true,
            error: null,
            
            // Data states
            kpi: { total: 0, clean: 0, check_in: 0, check_out: 0, dirty: 0, make_up_room: 0, inspected: 0, out_of_service: 0, out_of_order: 0, house_use: 0 },
            roomTypes: [],
            rooms: [],
            roomTypeOptions: [],
            
            // Filter states
            filters: {
                state: false,
                room_type_id: false,
                floor: false,
                start_date: false,
                end_date: false,
            },
            
            // UI states
            lastUpdated: null,
            filterValidationErrors: [],
            hasActiveFilters: false,
            
            // Pagination states
            currentPage: 1,
            pageSize: 100,
            totalPages: 1,
        });

        // Debounce timer for filter changes
        this.filterDebounceTimer = null;
        
        // State change history for debugging
        this.stateHistory = [];
    }

    initializeWatchers() {
        // Watch for filter changes
        this.watchFilters();
        
        // Watch for loading state changes
        this.watchLoadingState();
        
        // Watch for error state changes
        this.watchErrorState();
    }

    initializePersistence() {
        // Load saved state from localStorage
        this.loadStateFromStorage();
        
        // Save state changes to localStorage
        this.setupStatePersistence();
    }

    // Watchers for reactive state management
    watchFilters() {
        // Simple watcher for filters - OWL will handle reactivity
        // We'll use a different approach that's compatible with OWL
        this._previousFilters = { ...this.state.filters };
    }

    watchLoadingState() {
        // Simple watcher for loading state - OWL will handle reactivity
        // We'll use a different approach that's compatible with OWL
        this._previousLoading = this.state.loading;
    }

    watchErrorState() {
        // Simple watcher for error state - OWL will handle reactivity
        // We'll use a different approach that's compatible with OWL
        this._previousError = this.state.error;
    }

    // Computed properties
    updateComputedProperties() {
        // Update hasActiveFilters
        this.state.hasActiveFilters = this.hasActiveFilters();
        
        // Update filter validation errors (without triggering validation again)
        const validationErrors = this.validateFilters();
        this.state.filterValidationErrors = validationErrors;
        
        // Update pagination
        this.updatePagination();
    }

    hasActiveFilters() {
        return Object.values(this.state.filters).some(value => 
            value !== false && value !== null && value !== undefined && value !== ''
        );
    }

    updatePagination() {
        const totalRooms = this.state.rooms.length;
        this.state.totalPages = Math.ceil(totalRooms / this.state.pageSize);
        
        // Ensure current page is within bounds
        if (this.state.currentPage > this.state.totalPages) {
            this.state.currentPage = Math.max(1, this.state.totalPages);
        }
    }

    // State change logging
    logStateChange(section, property, oldValue, newValue) {
        const change = {
            timestamp: new Date().toISOString(),
            section,
            property,
            oldValue,
            newValue,
            stack: new Error().stack
        };
        
        this.stateHistory.push(change);
        
        // Keep only last 50 changes
        if (this.stateHistory.length > 50) {
            this.stateHistory = this.stateHistory.slice(-50);
        }
        
        console.log(`State change: ${section}.${property}`, change);
    }


    // State persistence
    loadStateFromStorage() {
        try {
            const savedState = localStorage.getItem('hotel_dashboard_state');
            if (savedState) {
                const parsedState = JSON.parse(savedState);
                
                // Only restore safe properties
                if (parsedState.filters) {
                    // Check if filters are valid before restoring
                    const validFilters = this.validateRestoredFilters(parsedState.filters);
                    this.state.filters = { ...this.state.filters, ...validFilters };
                }
                
                if (parsedState.pageSize) {
                    this.state.pageSize = parsedState.pageSize;
                }
                
                console.log('State restored from localStorage:', parsedState);
            }
        } catch (error) {
            console.warn('Failed to load state from localStorage:', error);
        }
    }

    validateRestoredFilters(filters) {
        // Validate and clean restored filters
        const validFilters = {};
        
        // Only restore filters that have valid values
        if (filters.state && ['clean', 'dirty', 'make_up_room', 'inspected', 'out_of_service', 'out_of_order', 'house_use'].includes(filters.state)) {
            validFilters.state = filters.state;
        }
        
        if (filters.room_type_id && typeof filters.room_type_id === 'number' && filters.room_type_id > 0) {
            validFilters.room_type_id = filters.room_type_id;
        }
        
        if (filters.floor && typeof filters.floor === 'number' && filters.floor > 0) {
            validFilters.floor = filters.floor;
        }
        
        if (filters.start_date && filters.end_date) {
            validFilters.start_date = filters.start_date;
            validFilters.end_date = filters.end_date;
        }
        
        console.log('Validated restored filters:', validFilters);
        return validFilters;
    }

    saveStateToStorage() {
        try {
            const stateToSave = {
                filters: this.state.filters,
                pageSize: this.state.pageSize,
                lastSaved: new Date().toISOString()
            };
            
            localStorage.setItem('hotel_dashboard_state', JSON.stringify(stateToSave));
            console.log('State saved to localStorage:', stateToSave);
        } catch (error) {
            console.warn('Failed to save state to localStorage:', error);
        }
    }

    setupStatePersistence() {
        // Save state on filter changes
        const originalApplyFilters = this.applyFilters.bind(this);
        this.applyFilters = async () => {
            await originalApplyFilters();
            this.saveStateToStorage();
        };
    }

    // State change handlers
    handleLoadingStateChange(isLoading) {
        if (isLoading) {
            console.log('Loading started...');
        } else {
            console.log('Loading completed...');
        }
    }

    handleErrorStateChange(error) {
        if (error) {
            console.error('Error occurred:', error);
            // You can add UI notification here
        } else {
            console.log('Error cleared');
        }
    }

    // Advanced state management methods
    resetState() {
        console.log('Resetting state to initial values...');
        
        this.state.loading = true;
        this.state.error = null;
        this.state.kpi = { total: 0, available: 0, occupied: 0, reserved: 0, dirty: 0, inspected: 0, clean: 0, oos: 0 };
        this.state.roomTypes = [];
        this.state.rooms = [];
        this.state.lastUpdated = null;
        this.state.filterValidationErrors = [];
        this.state.hasActiveFilters = false;
        this.state.currentPage = 1;
        this.state.totalPages = 1;
        
        // Reset filters
        this.state.filters = {
            state: false,
            room_type_id: false,
            floor: false,
            start_date: false,
            end_date: false,
        };
        
        // Clear state history
        this.stateHistory = [];
        
        console.log('State reset completed');
    }

    getStateSnapshot() {
        return {
            timestamp: new Date().toISOString(),
            loading: this.state.loading,
            error: this.state.error,
            kpi: { ...this.state.kpi },
            filters: { ...this.state.filters },
            hasActiveFilters: this.state.hasActiveFilters,
            filterValidationErrors: [...this.state.filterValidationErrors],
            currentPage: this.state.currentPage,
            totalPages: this.state.totalPages,
            roomsCount: this.state.rooms.length,
            roomTypesCount: this.state.roomTypes.length,
        };
    }

    restoreStateSnapshot(snapshot) {
        if (!snapshot || !snapshot.timestamp) {
            console.warn('Invalid state snapshot provided');
            return false;
        }
        
        try {
            console.log('Restoring state from snapshot:', snapshot.timestamp);
            
            // Restore safe properties
            if (snapshot.filters) {
                this.state.filters = { ...snapshot.filters };
            }
            
            if (snapshot.currentPage) {
                this.state.currentPage = snapshot.currentPage;
            }
            
            if (snapshot.totalPages) {
                this.state.totalPages = snapshot.totalPages;
            }
            
            console.log('State restored successfully');
            return true;
        } catch (error) {
            console.error('Failed to restore state snapshot:', error);
            return false;
        }
    }

    // State validation
    validateState() {
        const errors = [];
        
        // Validate filters
        const filterErrors = this.validateFilters();
        if (filterErrors.length > 0) {
            errors.push(...filterErrors.map(err => `Filter: ${err}`));
        }
        
        // Validate pagination
        if (this.state.currentPage < 1) {
            errors.push('Current page must be >= 1');
        }
        
        if (this.state.pageSize < 1) {
            errors.push('Page size must be >= 1');
        }
        
        // Validate data consistency
        if (this.state.rooms.length > 0 && this.state.roomTypes.length === 0) {
            errors.push('Rooms exist but no room types found');
        }
        
        return errors;
    }

    // State debugging
    getStateDebugInfo() {
        return {
            stateSnapshot: this.getStateSnapshot(),
            stateHistory: this.stateHistory.slice(-10), // Last 10 changes
            validationErrors: this.validateState(),
            memoryUsage: this.getMemoryUsage(),
            performanceMetrics: this.getPerformanceMetrics(),
        };
    }

    getMemoryUsage() {
        if (performance.memory) {
            return {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + ' MB',
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + ' MB',
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024) + ' MB',
            };
        }
        return { used: 'N/A', total: 'N/A', limit: 'N/A' };
    }

    getPerformanceMetrics() {
        return {
            stateChanges: this.stateHistory.length,
            lastStateChange: this.stateHistory[this.stateHistory.length - 1]?.timestamp || 'None',
            debounceTimerActive: !!this.filterDebounceTimer,
            hasActiveFilters: this.state.hasActiveFilters,
        };
    }

    buildFilterDomain() {
        const domain = [];
        
        // Debug: Log current filter state
        console.log("Current filter state:", this.state.filters);
        
        // Apply state filter
        if (this.state.filters.state) {
            domain.push(["state", "=", this.state.filters.state]);
            console.log("Added state filter:", this.state.filters.state);
        }
        
        // Apply room type filter
        if (this.state.filters.room_type_id) {
            domain.push(["room_type_id", "=", this.state.filters.room_type_id]);
            console.log("Added room type filter:", this.state.filters.room_type_id);
        }
        
        // Apply floor filter
        if (this.state.filters.floor) {
            domain.push(["floor", "=", this.state.filters.floor]);
            console.log("Added floor filter:", this.state.filters.floor);
        }
        
        // Apply date range filter (if needed for room availability)
        if (this.state.filters.start_date && this.state.filters.end_date) {
            // For now, we'll apply date filters to room blocking check
            // This can be extended based on your business logic
            console.log("Date filters applied:", {
                start_date: this.state.filters.start_date,
                end_date: this.state.filters.end_date
            });
        }
        
        console.log("Built filter domain:", domain);
        return domain;
    }

    buildRoomTypeFilterDomain() {
        const domain = [];
        
        // If room type is filtered, only show that room type
        if (this.state.filters.room_type_id) {
            domain.push(["id", "=", this.state.filters.room_type_id]);
        }
        
        return domain;
    }

    async loadData() {
        try {
            console.log("Loading dashboard data...");
            
            // Set loading state safely
            this.state.loading = true;
            this.state.error = null;
            
            // Build filter domain for all queries
            const baseDomain = this.buildFilterDomain();
            
            // Debug: Check if there are any rooms at all
            console.log("Base domain for KPI queries:", baseDomain);
            
            // KPI counts with filters applied
            const total = await this.orm.searchCount("hotel.room", baseDomain);
            console.log("Total rooms found:", total);
            
            const clean = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "clean"]]);
            const check_in = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "check_in"]]);
            const check_out = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "check_out"]]);
            const dirty = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "dirty"]]);
            const make_up_room = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "make_up_room"]]);
            const inspected = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "inspected"]]);
            const out_of_service = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "out_of_service"]]);
            const out_of_order = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "out_of_order"]]);
            const house_use = await this.orm.searchCount("hotel.room", [...baseDomain, ["state", "=", "house_use"]]);
            
            console.log("KPI counts:", { total, clean, check_in, check_out, dirty, make_up_room, inspected, out_of_service, out_of_order, house_use });

            // Update KPI data
            this.state.kpi = { total, clean, check_in, check_out, dirty, make_up_room, inspected, out_of_service, out_of_order, house_use };

            // Room types with filters applied
            const roomTypeDomain = this.buildRoomTypeFilterDomain();
            console.log("Room type domain:", roomTypeDomain);
            
            const roomTypes = await this.orm.searchRead("hotel.room.type", roomTypeDomain, ["name", "code", "room_count"], { limit: 50 });
            console.log("Room types found:", roomTypes);
            
            // Calculate available rooms for each room type
            const roomTypesWithAvailability = await Promise.all(
                roomTypes.map(async (rt) => {
                    // Debug: Log the queries being made
                    const availableDomain = [
                        ...baseDomain,
                        ["room_type_id", "=", rt.id],
                        ["state", "in", ["clean", "inspected"]]
                    ];
                    const totalDomain = [
                        ...baseDomain,
                        ["room_type_id", "=", rt.id]
                    ];
                    
                    console.log(`Calculating availability for room type ${rt.name} (ID: ${rt.id})`);
                    console.log("Available domain:", availableDomain);
                    console.log("Total domain:", totalDomain);
                    
                    const availableCount = await this.orm.searchCount("hotel.room", availableDomain);
                    const totalCount = await this.orm.searchCount("hotel.room", totalDomain);
                    
                    console.log(`Room type ${rt.name}: total=${totalCount}, available=${availableCount}`);
                    
                    return {
                        room_type_id: rt.id,
                        name: rt.name,
                        code: rt.code,
                        total_rooms: totalCount,
                        available_rooms: availableCount,
                        availability_rate: totalCount > 0 ? (availableCount / totalCount) * 100 : 0
                    };
                })
            );
            
            this.state.roomTypes = roomTypesWithAvailability;
            this.state.roomTypeOptions = roomTypes.map((r) => ({ id: r.id, name: r.name }));

            // Rooms list with filters applied
            const rooms = await this.orm.searchRead("hotel.room", baseDomain, [
                "room_number", "floor", "room_type_id", "state", 
                "maintenance_required"
            ], { limit: 100 });
            
            console.log("Rooms found:", rooms);
            console.log("Sample room data:", rooms.slice(0, 3));
            
            this.state.rooms = rooms;
            this.state.loading = false;
            this.state.lastUpdated = new Date().toLocaleTimeString();
            
            console.log("Dashboard data loaded successfully", {
                kpi: this.state.kpi,
                roomsCount: this.state.rooms.length,
                lastUpdated: this.state.lastUpdated,
                filters: this.state.filters
            });
            
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            
            // Set error state
            this.state.loading = false;
            this.state.error = error.message || "Unknown error occurred";
            this.state.kpi = { total: 0, available: 0, occupied: 0, reserved: 0, dirty: 0, inspected: 0, clean: 0, oos: 0 };
            this.state.roomTypes = [];
            this.state.rooms = [];
        }
    }

    async applyFilters() {
        console.log("Applying filters...");
        
        // Validate filters before applying
        const validationErrors = this.validateFilters();
        if (validationErrors.length > 0) {
            console.warn("Filter validation errors:", validationErrors);
            this.state.filterValidationErrors = validationErrors;
        } else {
            this.state.filterValidationErrors = [];
        }
        
        // Update computed properties
        this.updateComputedProperties();
        
        console.log("Filters applied:", this.state.filters);
        console.log("Active filters:", this.getFilterSummary());
        
        // Reload data with new filters
        await this.loadData();
    }

    async clearFilters() {
        console.log("Clearing filters...");
        
        // Reset filters state - OWL will automatically update the UI
        this.state.filters = {
            state: false,
            room_type_id: false,
            floor: false,
            start_date: false,
            end_date: false,
        };
        
        console.log("Filters cleared");
        
        // Clear localStorage as well
        try {
            localStorage.removeItem('hotel_dashboard_state');
            console.log('Stored state cleared from localStorage');
        } catch (error) {
            console.warn('Failed to clear stored state:', error);
        }
        
        // Reload data with cleared filters
        await this.loadData();
    }

    // OWL Reactive Methods for individual filter changes with debouncing
    onStateChange(ev) {
        const value = ev.target.value;
        this.state.filters.state = value || false;
        console.log("State changed:", value);
        this.debouncedApplyFilters();
    }

    onRoomTypeChange(ev) {
        const value = ev.target.value;
        this.state.filters.room_type_id = value ? parseInt(value) : false;
        console.log("Room type changed:", value);
        this.debouncedApplyFilters();
    }

    onFloorChange(ev) {
        const value = ev.target.value;
        this.state.filters.floor = value ? parseInt(value) : false;
        console.log("Floor changed:", value);
        this.debouncedApplyFilters();
    }

    onStartDateChange(ev) {
        const value = ev.target.value;
        this.state.filters.start_date = value || false;
        console.log("Start date changed:", value);
        this.debouncedApplyFilters();
    }

    onEndDateChange(ev) {
        const value = ev.target.value;
        this.state.filters.end_date = value || false;
        console.log("End date changed:", value);
        this.debouncedApplyFilters();
    }

    // Debounced filter application to prevent too many API calls
    debouncedApplyFilters() {
        if (this.filterDebounceTimer) {
            clearTimeout(this.filterDebounceTimer);
        }
        
        this.filterDebounceTimer = setTimeout(() => {
            this.applyFilters();
        }, 300); // 300ms delay
    }

    // Method to handle filter state changes reactively
    onFilterChange(filterName, value) {
        console.log(`Filter ${filterName} changed:`, value);
        
        // Update the specific filter in state
        this.state.filters[filterName] = value || false;
        
        // Apply debounced filters
        this.debouncedApplyFilters();
    }

    // Method to get current filter values for debugging
    getCurrentFilters() {
        return {
            state: this.state.filters.state,
            room_type_id: this.state.filters.room_type_id,
            floor: this.state.filters.floor,
            start_date: this.state.filters.start_date,
            end_date: this.state.filters.end_date,
        };
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

    // Helper method for debugging filter state
    getFilterSummary() {
        const activeFilters = Object.entries(this.state.filters)
            .filter(([key, value]) => value && value !== false)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ');
        
        return activeFilters || 'No filters applied';
    }

    // Helper method to validate filter values
    validateFilters() {
        const errors = [];
        
        if (this.state.filters.start_date && this.state.filters.end_date) {
            const startDate = new Date(this.state.filters.start_date);
            const endDate = new Date(this.state.filters.end_date);
            
            if (startDate > endDate) {
                errors.push('Start date must be before end date');
            }
        }
        
        if (this.state.filters.floor && (this.state.filters.floor < 1 || this.state.filters.floor > 100)) {
            errors.push('Floor must be between 1 and 100');
        }
        
        return errors;
    }
}

HotelDashboard.template = "modulio_hotelcore.HotelDashboard";

registry.category("actions").add("hotel_dashboard", HotelDashboard);

export default HotelDashboard;


