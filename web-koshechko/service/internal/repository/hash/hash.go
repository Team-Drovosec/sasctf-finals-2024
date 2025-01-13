package hash

import (
	"errors"
	"math/big"
)

// WARNING: don't change this constants

var (
	n = big.NewInt(0)
	e = big.NewInt(65537)
)

func init() {
	n.SetString("28757011453696365537010943219256697514126823462382199267523807215656057927126938852532938273735278647439093723114415999527098723727976475936319155015427799997213003664499422631017367287332875193524677851189982495235297707215042033048262623778358190536462998154798211571895963976626619781876160386784876909081999350085274414471035318193235136484576917339366720845318413892930365483764728962401235587394114713997688753422002084296070311024847072828816942070893651675293360209965132732838522510660772870550822829094375086110109463351493357171504313446493634012225805624774006426508038811853036507008224435127381274346463", 10)
}

func stringToBigInt(s string) (*big.Int, error) {
	if len(s) == 0 {
		return nil, nil
	}

	b := big.NewInt(int64(s[0]))
	for _, c := range s[1:] {
		b = b.Mul(b, big.NewInt(int64(c)))
	}
	return b, nil
}

func Hash(x string) (string, error) {
	inp, err := stringToBigInt(x)
	if err != nil {
		return "", err
	}

	c := big.NewInt(0)
	c = c.Exp(inp, e, n)

	return c.String(), nil
}

func AddHash(passHash, addedText string) (string, error) {
	pass := big.NewInt(0)
	pass, ok := pass.SetString(passHash, 10)
	if !ok {
		return "", errors.New("wtf")
	}

	add, err := stringToBigInt(addedText)
	if err != nil {
		return "", err
	}

	c := big.NewInt(0)
	c = c.Exp(add, e, n)

	res := big.NewInt(0)
	res = res.Mul(pass, c)
	res = res.Mod(res, n)

	return res.String(), nil
}
