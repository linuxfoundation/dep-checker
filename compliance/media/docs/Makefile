default: index.html

index.html.addons:
	./text-docs-to-html > index.html.addons

index.html: index.html.addons
	cat index.html.base index.html.addons index.html.footer > index.html

clean:
	rm -f index.html index.html.addons
