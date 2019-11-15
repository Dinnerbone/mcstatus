import click
from json import dumps as json_dumps

from .. import MinecraftServer

server = None


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
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
    click.echo("description: \"{}\"".format(response.description))
    click.echo(
        "players: {}/{} {}".format(
            response.players.online,
            response.players.max,
            [
                "{} ({})".format(player.name, player.id)
                for player in response.players.sample
            ] if response.players.sample is not None else "No players online"
        )
    )


@cli.command(short_help="all available server information in json")
def json():
    """
    Prints server status and query in json. Supported by all Minecraft
    servers that are version 1.7 or higher.
    """
    try:
        response1 = server.ping()
    except:
        response1 = None
    data = {
        'online': response1 is not None
    }
    if data['online']:
        response2 = server.status(retries=1)
        try:
            response3 = server.query(retries=1)
        except Exception:
            response3 = None
        data['online'] = True
        data['ping'] = response1
        data['version'] = response2.version.name
        data['protocol'] = response2.version.protocol
        data['motd'] = response2.description
        data['player_count'] = response2.players.online
        data['player_max'] = response2.players.max
        data['players'] = []
        if response2.players.sample is not None:
            data['players'] = [{'name': player.name, 'id': player.id} for player in response2.players.sample]
        if response3 is not None:
            data['host_ip'] = response3.raw['hostip']
            data['host_port'] = response3.raw['hostport']
            data['map'] = response3.map
            data['plugins'] = response3.software.plugins
    click.echo(json_dumps(data))


@cli.command(short_help="detailed server information")
def query():
    """
    Prints detailed server information. Must be enabled in
    servers' server.properties file.
    """
    response = server.query()
    click.echo("host: {}:{}".format(response.raw['hostip'], response.raw['hostport']))
    click.echo("software: v{} {}".format(response.software.version, response.software.brand))
    click.echo("plugins: {}".format(response.software.plugins))
    click.echo("motd: \"{}\"".format(response.motd))
    click.echo(
        "players: {}/{} {}".format(
            response.players.online,
            response.players.max,
            response.players.names,
        )
    )


if __name__ == "__main__":
    cli()
