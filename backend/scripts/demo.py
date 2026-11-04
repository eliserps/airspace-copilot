import asyncio

from app.container import build_services
from app.core.config import Language, configure_tls, get_settings
from app.core.logging import configure_logging

REGION = "south_america"
AIRPORTS = ["SBGR", "SBGL", "SBPA"]
LANGUAGE: Language = "pt"
QUESTIONS = [
    "Como está o tempo para pouso em Porto Alegre?",
    "Quantos aviões estão sobre a América do Sul agora?",
]


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_tls(settings)
    services = build_services(settings)
    try:
        snapshot = await services.traffic.snapshot(REGION)
        print(f"{len(snapshot.aircraft)} aircraft detected\n")

        print("--- DECODED WEATHER ---")
        for airport in AIRPORTS:
            metar = await services.metar.latest(airport)
            print(f"\n[{airport}] raw: {metar!r}")
            if metar:
                print(await services.decoder.decode(metar, LANGUAGE))

        print(f"\n--- BRIEFING ({LANGUAGE.upper()}) ---")
        briefing = await services.briefing.generate(snapshot.aircraft, REGION, LANGUAGE)
        print(briefing.text)

        print("\n--- COPILOT ---")
        for question in QUESTIONS:
            print(f"\n> {question}")
            async for chunk in services.agent.stream(question, REGION):
                print(chunk, end="", flush=True)
            print()
    finally:
        await services.aclose()


if __name__ == "__main__":
    asyncio.run(main())
