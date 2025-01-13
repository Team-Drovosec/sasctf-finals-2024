package model

const PublicKoshechko = 0

type Koshechko struct {
	ID         int64
	Name       string
	Owner      string
	Text       string
	SharedWith []string
}
