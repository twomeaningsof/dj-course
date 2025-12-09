package time_locks

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	"tms-data-generator/generator/drivers"
	"tms-data-generator/generator/transportation_orders"
	"tms-data-generator/generator/vehicles"
)

// GenerateTimeLocks generates a slice of TimeLock structs.
func GenerateTimeLocks(count int, drivers []drivers.Driver, vehicles []vehicles.Vehicle, orders []transportation_orders.TransportationOrder) []TimeLock {
	timeLocks := make([]TimeLock, count)

	for i := 0; i < count; i++ {
		lockType := []LockType{LockTypeRoute, LockTypeVacation, LockTypeMaintenance}[rand.Intn(3)]

		var driverID *int
		var vehicleID *int
		var orderID *int

		startTime := time.Now().AddDate(0, 0, -rand.Intn(365)).Add(time.Duration(rand.Intn(24)) * time.Hour)
		endTime := startTime.Add(time.Duration(rand.Intn(48)+1) * time.Hour) // 1 to 48 hours

		switch lockType {
		case LockTypeRoute:
			// For 'TRASA', all three IDs must be present
			drvrID := drivers[rand.Intn(len(drivers))].ID
			driverID = &drvrID

			vehID := vehicles[rand.Intn(len(vehicles))].ID
			vehicleID = &vehID

			ordID := orders[rand.Intn(len(orders))].ID
			orderID = &ordID
		case LockTypeVacation:
			// For 'URLOP/L4', only driver_id is present
			drvrID := drivers[rand.Intn(len(drivers))].ID
			driverID = &drvrID
		case LockTypeMaintenance:
			// For 'SERWIS', only vehicle_id is present
			vehID := vehicles[rand.Intn(len(vehicles))].ID
			vehicleID = &vehID
		}

		timeLocks[i] = TimeLock{
			ID:                  i + 1,
			DriverID:            driverID,
			VehicleID:           vehicleID,
			StartTime:           startTime,
			EndTime:             endTime,
			LockType:            lockType,
			TransportationOrderID: orderID,
		}
	}

	return timeLocks
}

// GenerateInsertStatements generates SQL INSERT statements for time locks.
func GenerateInsertStatements(timeLocks []TimeLock) string {
	if len(timeLocks) == 0 {
		return ""
	}

	var sb strings.Builder
	sb.Grow(len(timeLocks) * 200) // Pre-allocate approximate size

	sb.WriteString("INSERT INTO time_locks (id, driver_id, vehicle_id, start_time, end_time, lock_type, transportation_order_id) VALUES\n")

	for i, tl := range timeLocks {
		sb.WriteString(fmt.Sprintf("    (%d, ", tl.ID))

		if tl.DriverID != nil {
			sb.WriteString(fmt.Sprintf("%d, ", *tl.DriverID))
		} else {
			sb.WriteString("NULL, ")
		}

		if tl.VehicleID != nil {
			sb.WriteString(fmt.Sprintf("%d, ", *tl.VehicleID))
		} else {
			sb.WriteString("NULL, ")
		}

		sb.WriteString(fmt.Sprintf("'%s', '%s', '%s', ",
			tl.StartTime.Format("2006-01-02 15:04:05"),
			tl.EndTime.Format("2006-01-02 15:04:05"),
			tl.LockType))

		if tl.TransportationOrderID != nil {
			sb.WriteString(fmt.Sprintf("%d)", *tl.TransportationOrderID))
		} else {
			sb.WriteString("NULL)")
		}

		if i < len(timeLocks)-1 {
			sb.WriteString(",\n")
		} else {
			sb.WriteString(";\n")
		}
	}

	return sb.String()
}
