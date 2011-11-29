import os
import context_managers
import utils
import operations

from fabric.api import env, require, cd, runs_once, sudo, abort

@runs_once
def setup_paths():
    require("play_root", "project_name")

    env.project_path = os.path.join(env.play_root, env.project_name)
    env.config_source = os.path.join("conf", "application.conf.template")
    env.config_target = os.path.join("conf", "application.conf")


def sync_deps():
    """
    """

    require(
        "project_path",
        "http_proxy",
        "https_proxy",
        "sudo_user",
    )
    with context_managers.proxy(env.http_proxy, env.https_proxy):
        utils.play_run(env.project_path, "dependencies --sync", user=env.sudo_user)


def restart():
    """
    """

    require("project_name")

    cmd = "supervisorctl restart play-%s" % env.project_name
    sudo(cmd, shell=False)


@runs_once
def migratedb():
    """
    """

    require("project_path", "sudo_user")
    utils.play_run(env.project_path, "evolutions:apply", user=env.sudo_user)


def fetch_render_copy(ref=None, debug=False, dirty=False, copy_remote=False):
    """
    Fetch source code, render settings file, push remotely and delete checkout.
    """

    require("scm_type", "scm_url", "config_source", "config_target", "settings_vars")

    env.tempdir = utils.fetch_source(env.scm_type, env.scm_url, ref, dirty)
    config_source = os.path.join(env.tempdir, env.config_source)
    config_target = os.path.join(env.tempdir, env.config_target)
    utils.render_settings_template(config_source, config_target, env.settings_vars, debug)

    if copy_remote:
        operations.rsync_from_local()

    utils.delete_source(env.tempdir, dirty)


def deploy_play(ref=None, debug=False, dirty=False):
    """
    Standard Play deployment actions.
    """

    fetch_render_copy(ref, debug, dirty, True)
    sync_deps()
    migratedb()
    restart()
