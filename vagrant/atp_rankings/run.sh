#!/bin/bash
rm ../tournament/atp_rankings.json
scrapy crawl atp_rankings -o ../tournament/atp_rankings.json
