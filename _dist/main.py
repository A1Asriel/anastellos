from anastellos.engine import AnastellosEngine
from anastellos.logger import setupLogging

if __name__ == '__main__':
    additional_guild_params = {
        # "name": ('str', 'Your string here')
        # "enabled_responses": ('bool', False),
        # "telemetry": ('channel', 0)
    }
    additional_global_params = {
        # "test": "default value",
        # "boolean_works_too": True,
        # "so_do_integers": 255
    }
    setupLogging()
    engine = AnastellosEngine(additional_guild_params=additional_guild_params,
                              additional_global_params=additional_global_params)
    engine.load_cogs()
    engine.start()
