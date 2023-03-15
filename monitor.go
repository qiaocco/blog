package main

import (
	"log"
	"net/http"
)

const url = "https://blog.qiaocco.com"

func main(){
	resp, err := http.Get(url)
	if err!= nil{
		log.Fatalf("failed to get url")
		return
	}
	if resp.StatusCode != http.StatusOK{
		log.Fatalf("status not ok, %v", resp.StatusCode)
		return
	}

	log.Println("visit successfully")
}
