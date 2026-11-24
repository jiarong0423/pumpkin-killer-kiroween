"""Reference-path resolution for Colab asset queues."""


def resolve_refs(job, ref_table):
    """Return a job's reference paths in its declared order."""
    names = job.get("refs")
    if names is None:
        names = [job["ref"]]
    elif not isinstance(names, list):
        raise ValueError("job refs must be a list")

    paths = []
    for name in names:
        try:
            paths.append(ref_table[name])
        except KeyError as error:
            raise ValueError(f"unknown reference name: {name!r}") from error
    return paths
