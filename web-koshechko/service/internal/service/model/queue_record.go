package model

type EventType int64

const (
	ETIncKoshechko EventType = iota
	ETIncUser
	ETDelKoshechko
	ETDelUser
	ETIncFriends
	ETUpdateKoshechko
)

type QueueRecord struct {
	Id                  int64
	EventType           EventType
	Username            string
	KoshechkoName       string
	SharedCount         int64
	KoshechkoNewName    string
	KoshechkoText       string
	KoshechkoSharedWith []string
}
