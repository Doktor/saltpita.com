from invoke import task


manage = "pipenv run python manage.py"


@task
def build(ctx):
    print("Rebuilding stylesheets")
    with ctx.cd('static'):
        ctx.run("sass --update .:.")

    print("Collecting static files")
    ctx.run(f"{manage} collectstatic --no-input")

    print("Done!")
