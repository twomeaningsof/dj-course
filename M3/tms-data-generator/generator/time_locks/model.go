package time_locks

import (
	"time"
)

type LockType string

const (
	LockTypeRoute      LockType = "TRASA"
	LockTypeVacation   LockType = "URLOP/L4"
	LockTypeMaintenance LockType = "SERWIS"
)

type TimeLock struct {
	ID                  int
	DriverID            *int // Use pointer for nullable fields
	VehicleID           *int // Use pointer for nullable fields
	StartTime           time.Time
	EndTime             time.Time
	LockType            LockType
	TransportationOrderID *int // Use pointer for nullable fields
}
