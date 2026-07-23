import asyncio
from dataclasses import dataclass, field
from typing import Callable

import discord

MAX_ERRORS = 20


@dataclass
class MassAssignJob:
    status: str  # "running" | "completed" | "failed"
    total: int
    guild_id: int = 0
    processed: int = 0
    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list = field(default_factory=list)


JOBS: dict[str, MassAssignJob] = {}


def has_running_job(guild_id: int) -> bool:
    return any(job.status == "running" and int(job.guild_id) == int(guild_id) for job in JOBS.values())


async def run_mass_assign(
    job_id: str,
    guild,
    role,
    members: list,
    moderator,
    dashboard_reason: Callable[[str, object], str],
) -> None:
    job = JOBS[job_id]
    semaphore = asyncio.Semaphore(3)

    async def process(member) -> None:
        if any(r.id == role.id for r in member.roles):
            job.skipped += 1
        else:
            async with semaphore:
                try:
                    await member.add_roles(
                        role,
                        reason=dashboard_reason(f"массовая выдача роли {role.name}", moderator),
                    )
                    job.succeeded += 1
                except discord.HTTPException as exc:
                    job.failed += 1
                    if len(job.errors) < MAX_ERRORS:
                        job.errors.append(f"{member.name}: {exc}")
        job.processed += 1

    await asyncio.gather(*(process(member) for member in members))
    job.status = "completed"
