
test:
	python pyXsd2Xml.py --xsd-file=example.xsd > example.xml
	diff -q example.xml example.xml.ref && echo 'Test OK.' || echo "Test FAILED."
