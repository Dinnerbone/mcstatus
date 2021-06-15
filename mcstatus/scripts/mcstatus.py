import socket
from typing import Any
import click
from json import dumps as json_dumps

from .. import MinecraftServer

server = None


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("address")
def cli(address):
    """
    mcstatus provides an easy way to query Minecraft servers for
    any information they can expose. It provides three modes of
    access: query, status, and ping.

    Examples:

    \b
    $ mcstatus example.org ping
    21.120ms

    \b
    $ mcstatus example.org:1234 ping
    159.903ms

    \b
    $ mcstatus example.org status
    version: v1.8.8 (protocol 47)
    description: "A Minecraft Server"
    players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

    \b
    $ mcstatus example.org query
    host: 93.148.216.34:25565
    software: v1.8.8 vanilla
    plugins: []
    motd: "A Minecraft Server"
    players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']
    """
    global server
    server = MinecraftServer.lookup(address)


@cli.command(short_help="prints server latency")
def ping():
    """
    Ping server for latency.
    """
    click.echo("{}ms".format(server.ping()))


@cli.command(short_help="basic server information")
def status():
    """
    Prints server status. Supported by all Minecraft
    servers that are version 1.7 or higher.
    """
    response = server.status()
    click.echo("version: v{} (protocol {})".format(response.version.name, response.version.protocol))
    click.echo('description: "{}"'.format(response.description))
    click.echo(
        "players: {}/{} {}".format(
            response.players.online,
            response.players.max,
            ["{} ({})".format(player.name, player.id) for player in response.players.sample]
            if response.players.sample is not None
            else "No players online",
        )
    )


@cli.command(short_help="all available server information in json")
def json():
    """
    Prints server status and query in json. Supported by all Minecraft
    servers that are version 1.7 or higher.
    """
    data = {}
    data["online"] = False
    # Build data with responses and quit on exception
    try:
        ping_res = server.ping()
        data["online"] = True
        data["ping"] = ping_res

        status_res = server.status(tries=1)
        data["version"] = status_res.version.name
        data["protocol"] = status_res.version.protocol
        data["motd"] = status_res.description
        data["player_count"] = status_res.players.online
        data["player_max"] = status_res.players.max
        data["players"] = []
        if status_res.players.sample is not None:
            data["players"] = [{"name": player.name, "id": player.id} for player in status_res.players.sample]

        query_res = server.query(tries=1)
        data["host_ip"] = query_res.raw["hostip"]
        data["host_port"] = query_res.raw["hostport"]
        data["map"] = query_res.map
        data["plugins"] = query_res.software.plugins
    except:
        pass
    click.echo(json_dumps(data))


@cli.command(short_help="detailed server information")
def query():
    """
    Prints detailed server information. Must be enabled in
    servers' server.properties file.
    """
    try:
        response = server.query()
    except socket.timeout:
        print(
            """The server did not respond to the query protocol.
              Please ensure that the server has enable-query turned on, and that the necessary port (same as server-port unless query-port is set) is open in any firewall(s).
              See https://wiki.vg/Query for further information."""
        )
        raise click.Abort()
    click.echo("host: {}:{}".format(response.raw["hostip"], response.raw["hostport"]))
    click.echo("software: v{} {}".format(response.software.version, response.software.brand))
    click.echo("plugins: {}".format(response.software.plugins))
    click.echo('motd: "{}"'.format(response.motd))
    click.echo(
        "players: {}/{} {}".format(
            response.players.online,
            response.players.max,
            response.players.names,
        )
    )


if __name__ == "__main__":
    cli()
