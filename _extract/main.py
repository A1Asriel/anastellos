from anastellos.engine import AnastellosEngine

if __name__ == '__main__':
    additional_guild_params = {
        # "name": ('str', 'Your string here')
        # "enabled_responses": ('bool', False),
        # "telemetry": ('channel', 0)
    }
    engine = AnastellosEngine(additional_guild_params=additional_guild_params)
    engine.load_cogs()
    engine.start()
