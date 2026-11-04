# syntax=docker/dockerfile:1.7

FROM stagex/pallet-nodejs AS build-stage

COPY --from=stagex/user-hugo-extended:0.161.1 /usr/bin/hugo /usr/local/bin/hugo

ARG hugobuildargs
ENV HUGO_BUILD_ARGS=$hugobuildargs

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN hugo ${HUGO_BUILD_ARGS}
# The search index. pagefind.yml limits it to each page's <main data-pagefind-body>.
RUN npx --no-install pagefind

FROM stagex/user-caddy

COPY --from=stagex/core-musl / /
COPY --from=build-stage /app/public /srv

# The pipeline extracts /srv and the target host's Caddy imports
# redirects.caddy from the deployed content root, so it ships inside /srv
# (static/redirects.caddy). This Caddyfile is for `docker run` locally only.
COPY <<'CADDY' /etc/caddy/Caddyfile
{
	auto_https off
	admin off
}

:80 {
	root * /srv
	encode gzip zstd

	# Legacy Omeka S URL repairs (301s, 410s). /files/{original,large,medium,square}
	# is intentionally absent: the fronting web server serves media from the file store.
	import /srv/redirects.caddy

	file_server
}
CADDY

ENV XDG_CONFIG_HOME=/tmp/caddy-config \
    XDG_DATA_HOME=/tmp/caddy-data

EXPOSE 80
ENTRYPOINT ["/usr/bin/caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
