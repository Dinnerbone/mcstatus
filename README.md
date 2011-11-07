MinecraftQuery
======

With 1.9 came a shiny new tool to allow native status querying in vanilla Minecraft servers.
This is a simple class designed to aid in retrieving any data from the servers.

See it in action: [http://dinnerbone.com/minecraft/tools/status/](http://dinnerbone.com/minecraft/tools/status/)

Protocol documention: [http://dinnerbone.com/blog/2011/10/14/minecraft-19-has-rcon-and-query/](http://dinnerbone.com/blog/2011/10/14/minecraft-19-has-rcon-and-query/)

Usage
-----------

    from status_query import MinecraftQuery
    
    query = MinecraftQuery("localhost", 25565)
    
    basic_status = query.get_status()
    print "The server has %d players" % (basic_status['numplayers'])
    
    full_info = query.get_rules()
    print "The server is on the map '%s'" % (full_info['map'])

Rights
-----------
Fully open. Go wild.