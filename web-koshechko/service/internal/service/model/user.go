package model

type User struct {
	Name         string
	Desc         string
	PasswordHash []byte
}
