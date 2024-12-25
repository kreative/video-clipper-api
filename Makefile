.PHONY: reqs 
reqs:
	pip install -r requirements.txt

.PHONY: act
act:
	echo "Activating Virtual Environment"
	pipenv shell

.PHONY: dev
run:
	doppler run -- flask run

.PHONY: test
test:
	pytest
