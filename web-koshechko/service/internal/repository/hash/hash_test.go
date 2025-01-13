package hash

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAddHash(t *testing.T) {
	a := "sfawfew"
	b := "add text"

	abx, err := Hash(a + b)
	assert.NoError(t, err)

	ax, err := Hash(a)
	assert.NoError(t, err)

	abx_2, err := AddHash(ax, b)
	assert.NoError(t, err)

	assert.Equal(t, abx, abx_2)
}
