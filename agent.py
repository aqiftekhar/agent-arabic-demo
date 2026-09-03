# import logging
# import asyncio

# from livekit import rtc, api
# from livekit.agents import (
#     Agent,
#     AgentSession,
#     JobContext,
#     JobProcess,
#     RoomInputOptions,
#     WorkerOptions,
#     cli,
#     function_tool,
#     RunContext,
# )
# from livekit.plugins import deepgram, openai, elevenlabs, silero, noise_cancellation
# from livekit.plugins.turn_detector.multilingual import MultilingualModel

# from config import Settings
# from faq_store import store as faq_store, load_all as load_all_faqs

# logger = logging.getLogger("va-almosafer")

# settings = Settings.load()
# load_all_faqs()

# CATEGORY_LABELS = {
#     "1": "الطيران",
#     "2": "الفنادق",
#     "3": "شاليهات+",
#     "4": "المدفوعات والرسوم",
# }

# SYSTEM_PROMPT = """
# أنت مساعد صوتي يمثل شركة "المسافر" (Almosafer). تحدث باللغة العربية فقط طوال المكالمة.

# القواعد:
# - إذا تحدث المتصل بلغة غير العربية، اعتذر بأدب واطلب منه التحدث بالعربية فقط.
# - اجعل كل إجاباتك مختصرة جدًا: سطرين إلى ثلاثة أسطر كحد أقصى ما لم يتطلب السؤال تفصيلاً أكبر.
# - عندما يسأل المتصل عن أي معلومة تتعلق بالحجز، الأسعار، الإلغاء، الاسترداد، الرسوم، أو أي سياسة، يجب عليك دائمًا استدعاء أداة search_faq أولاً، والإجابة فقط بناءً على المحتوى الذي تعيده الأداة.
# - لا تخترع أي معلومة عن الأسعار، الرسوم، أو السياسات. إذا لم تجد الأداة إجابة مناسبة، اعتذر وأخبر المتصل أنه يمكنه الضغط على صفر للتحدث مع أحد الموظفين.
# - إذا طلب المتصل التحدث إلى موظف، استخدم أداة route_to_operator.
# - لا تستخدم رموزًا يصعب نطقها بصوت عالٍ.
# """

# GREETING = (
#     "مرحبًا بك في المسافر. "
#     "للاستفسار عن الطيران اضغط واحد. للفنادق اضغط اثنين. لشاليهات بلس اضغط ثلاثة. "
#     "للمدفوعات والرسوم اضغط أربعة. للتحدث مع أحد موظفينا اضغط صفر. "
#     "ولسماع هذه القائمة مرة أخرى في أي وقت اضغط على مفتاح الشباك."
# )
# REPROMPT = (
#     "لم أستلم اختيارك. اضغط واحد للطيران، اثنين للفنادق، ثلاثة لشاليهات بلس، "
#     "أربعة للمدفوعات والرسوم، أو صفر للتحدث مع موظف."
# )
# INVALID_KEY = "عذرًا، هذا الخيار غير متاح. يرجى اختيار رقم من واحد إلى أربعة، أو صفر للموظف، أو الشباك للقائمة الرئيسية."
# TRANSFER_FAILED = "عذرًا، تعذر تحويل المكالمة الآن. يمكنك الاستمرار بسؤال المساعد الذكي بدلاً من ذلك."
# NO_INPUT_FALLBACK = (
#     "يمكنك التحدث معي مباشرة وسأحاول مساعدتك، أو اضغط على الشباك لسماع "
#     "قائمة الأقسام مرة أخرى، أو صفر للتحدث مع أحد موظفينا."
# )


# def category_selected_prompt(label: str) -> str:
#     return f"تفضل، اسألني عن أي شيء يخص {label}."


# class AlmosaferAgent(Agent):
#     def __init__(self, on_route_operator, get_active_category) -> None:
#         super().__init__(instructions=SYSTEM_PROMPT)
#         self._on_route_operator = on_route_operator
#         self._get_active_category = get_active_category

#     @function_tool
#     async def route_to_operator(self, context: RunContext) -> str:
#         """استدعِ هذه الأداة عندما يطلب المتصل التحدث إلى موظف أو عملية تحويل بشرية."""
#         await self._on_route_operator()
#         return "تم بدء عملية التحويل."

#     @function_tool
#     async def search_faq(self, context: RunContext, query: str) -> str:
#         """
#         ابحث في الأسئلة الشائعة الخاصة بالفئة المختارة حاليًا (الطيران/الفنادق/شاليهات+/المدفوعات).
#         استدعِ هذه الأداة دائمًا قبل الإجابة على أي سؤال يتعلق بسياسة أو سعر أو رسوم أو حجز.
#         query: نص يلخص سؤال المتصل بكلمات مفتاحية بالعربية.
#         """
#         category = self._get_active_category()
#         if not category:
#             return (
#                 "لا توجد فئة مختارة حاليًا. أخبر المتصل أن عليه اختيار قسم "
#                 "(الطيران، الفنادق، شاليهات+، أو المدفوعات والرسوم) أولاً."
#             )

#         results = faq_store.search(category, query, top_n=2)
#         if not results:
#             return (
#                 "لم يتم العثور على إجابة مطابقة في الأسئلة الشائعة لهذه الفئة. "
#                 "اعتذر للمتصل ولا تخترع إجابة، وأخبره أنه يمكنه الضغط على صفر للتحدث مع موظف."
#             )

#         blocks = []
#         for r in results:
#             blocks.append(f"سؤال: {r['question']}\nجواب: {r['answer']}")
#         return "\n\n".join(blocks)


# def prewarm(proc: JobProcess):
#     proc.userdata["vad"] = silero.VAD.load(
#         min_speech_duration=settings.vad_min_speech_duration,
#         min_silence_duration=settings.vad_min_silence_duration,
#         prefix_padding_duration=settings.vad_prefix_padding_duration,
#         activation_threshold=settings.vad_activation_threshold,
#     )


# async def entrypoint(ctx: JobContext):
#     await ctx.connect()

#     call_ended = asyncio.Event()
#     participant_holder = {}
#     state = {"active_category": None}

#     session = AgentSession(
#         vad=ctx.proc.userdata["vad"],
#         stt=deepgram.STT(model=settings.stt_model, language=settings.stt_language),
#         llm=openai.LLM(
#             model=settings.llm_model,
#             base_url=settings.llm_base_url,
#             api_key=settings.groq_api_key,
#             temperature=0.3,
#         ),
#         tts=elevenlabs.TTS(
#             model=settings.tts_model,
#             voice_id=settings.elevenlabs_voice_id,
#             api_key=settings.elevenlabs_api_key,
#         ),
#         # NOTE: MultilingualModel does not support Arabic ('ar') per SDK logs -
#         # left here only if you want the deprecated fallback; recommended to
#         # set turn_detection=None and rely on VAD-only endpointing instead.
#         turn_detection=MultilingualModel(),
#         min_endpointing_delay=settings.min_endpointing_delay,
#         max_endpointing_delay=settings.max_endpointing_delay,
#         preemptive_generation=True,
#     )

#     async def transfer_to_operator():
#         logger.info(f"Transferring caller to extension {settings.sip_transfer_extension}")
#         lkapi = api.LiveKitAPI(
#             url=settings.livekit_url,
#             api_key=settings.livekit_api_key,
#             api_secret=settings.livekit_api_secret,
#         )
#         try:
#             await lkapi.sip.transfer_sip_participant(
#                 api.TransferSIPParticipantRequest(
#                     room_name=ctx.room.name,
#                     participant_identity=participant_holder["p"].identity,
#                     transfer_to=settings.operator_sip_uri,
#                 )
#             )
#         except api.SipCallError as e:
#             logger.error(f"Transfer failed: {e}")
#             await session.say(TRANSFER_FAILED, allow_interruptions=True)
#         finally:
#             await lkapi.aclose()

#     async def route_operator_cb():
#         await transfer_to_operator()

#     def get_active_category():
#         return state["active_category"]

#     agent = AlmosaferAgent(
#         on_route_operator=route_operator_cb,
#         get_active_category=get_active_category,
#     )

#     # ---- DTMF handling: registered EARLY, before any speech starts ----
#     last_dtmf_time = 0.0

#     def on_dtmf(dtmf: rtc.SipDTMF):
#         nonlocal last_dtmf_time
#         loop = asyncio.get_event_loop()
#         now = loop.time()
#         if now - last_dtmf_time < settings.dtmf_debounce_seconds:
#             return
#         last_dtmf_time = now
#         asyncio.create_task(handle_dtmf(dtmf.digit))

#     async def handle_dtmf(digit: str):
#         # "0" -> operator, works at ANY point in the call, interrupts current speech
#         if digit == "0":
#             await session.interrupt()
#             await transfer_to_operator()
#             return

#         # "#" -> back to main menu, replay greeting
#         if digit == "#":
#             state["active_category"] = None
#             await session.interrupt()
#             await session.say(GREETING, allow_interruptions=True)
#             return

#         # "1".."4" -> select/switch category directly, even mid-conversation
#         if digit in CATEGORY_LABELS:
#             state["active_category"] = digit
#             label = CATEGORY_LABELS[digit]
#             await session.interrupt()
#             await session.say(category_selected_prompt(label), allow_interruptions=True)
#             return

#         # anything else -> invalid key
#         await session.interrupt()
#         await session.say(INVALID_KEY, allow_interruptions=True)

#     ctx.room.on("sip_dtmf_received", on_dtmf)

#     await session.start(
#         agent=agent,
#         room=ctx.room,
#         room_input_options=RoomInputOptions(
#             noise_cancellation=noise_cancellation.BVCTelephony(),
#         ),
#     )

#     participant = await ctx.wait_for_participant()
#     participant_holder["p"] = participant

#     async def enforce_max_duration():
#         try:
#             await asyncio.sleep(settings.max_call_duration_seconds)
#             if not call_ended.is_set():
#                 logger.info("Max call duration reached, ending call")
#                 lkapi = api.LiveKitAPI(
#                     url=settings.livekit_url,
#                     api_key=settings.livekit_api_key,
#                     api_secret=settings.livekit_api_secret,
#                 )
#                 try:
#                     await lkapi.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
#                 finally:
#                     await lkapi.aclose()
#         except asyncio.CancelledError:
#             pass

#     duration_task = asyncio.create_task(enforce_max_duration())

#     def on_disconnect(*_):
#         call_ended.set()
#         duration_task.cancel()

#     ctx.room.on("participant_disconnected", on_disconnect)

#     # Greeting is spoken AFTER the DTMF listener is live
#     await session.say(GREETING, allow_interruptions=True)

#     # ---- main-menu watchdog: re-prompt if no category chosen yet ----
#     async def menu_watchdog():
#         for _ in range(settings.menu_max_reprompts):
#             await asyncio.sleep(settings.menu_timeout_seconds)
#             if state["active_category"] is not None or call_ended.is_set():
#                 return
#             await session.say(REPROMPT, allow_interruptions=True)
#         if state["active_category"] is None and not call_ended.is_set():
#             await session.say(NO_INPUT_FALLBACK, allow_interruptions=True)

#     asyncio.create_task(menu_watchdog())


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=settings.agent_name))

import logging
import asyncio

from livekit import rtc, api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)

from livekit.plugins import deepgram, openai, elevenlabs, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from config import Settings
from faq_store import store as faq_store, load_all as load_all_faqs

logger = logging.getLogger("va-almosafer")

settings = Settings.load()
load_all_faqs()

CATEGORY_LABELS = {
    "1": "الطيران",
    "2": "الفنادق",
    "3": "شاليهات+",
    "4": "المدفوعات والرسوم",
}

SYSTEM_PROMPT = """
أنت مساعد صوتي يمثل شركة "المسافر" (Almosafer). تحدث باللغة العربية فقط طوال المكالمة.

القواعد:
- إذا تحدث المتصل بلغة غير العربية، اعتذر بأدب واطلب منه التحدث بالعربية فقط.
- اجعل كل إجاباتك مختصرة جدًا: سطرين إلى ثلاثة أسطر كحد أقصى ما لم يتطلب السؤال تفصيلاً أكبر.
- عندما يسأل المتصل عن أي معلومة تتعلق بالحجز، الأسعار، الإلغاء، الاسترداد، الرسوم، أو أي سياسة، يجب عليك دائمًا استدعاء أداة search_faq أولاً، والإجابة فقط بناءً على المحتوى الذي تعيده الأداة.
- لا تخترع أي معلومة عن الأسعار، الرسوم، أو السياسات. إذا لم تجد الأداة إجابة مناسبة، اعتذر وأخبر المتصل أنه يمكنه الضغط على صفر للتحدث مع أحد الموظفين.
- لا تقرأ نص الجواب المُعاد من الأداة حرفيًا وكاملاً. لخّصه بأسلوب طبيعي منطوق في جملتين إلى ثلاث جمل، مع الحفاظ الدقيق على كل رقم أو مبلغ أو شرط مذكور في الجواب الأصلي دون تغيير أو حذف.
- لا تنطق أبدًا أي رابط إلكتروني (URL) أو عنوان بريد إلكتروني بصوت عالٍ. إذا كان الجواب يتضمن رابطًا، استبدله بعبارة مثل "يمكنك التواصل مع فريق خدمة العملاء" دون ذكر الرابط نفسه.
- إذا طلب المتصل التحدث إلى موظف، استخدم أداة route_to_operator.
- لا تستخدم رموزًا يصعب نطقها بصوت عالٍ.
"""

GREETING = (
    "مرحبًا بك في المسافر. "
    "للاستفسار عن الطيران اضغط واحد. للفنادق اضغط اثنين. لشاليهات بلس اضغط ثلاثة. "
    "للمدفوعات والرسوم اضغط أربعة. للتحدث مع أحد موظفينا اضغط صفر. "
    "ولسماع هذه القائمة مرة أخرى في أي وقت اضغط على مفتاح الشباك."
)
REPROMPT = (
    "لم أستلم اختيارك. اضغط واحد للطيران، اثنين للفنادق، ثلاثة لشاليهات بلس، "
    "أربعة للمدفوعات والرسوم، أو صفر للتحدث مع موظف."
)
INVALID_KEY = "عذرًا، هذا الخيار غير متاح. يرجى اختيار رقم من واحد إلى أربعة، أو صفر للموظف، أو الشباك للقائمة الرئيسية."
TRANSFER_FAILED = "عذرًا، تعذر تحويل المكالمة الآن. يمكنك الاستمرار بسؤال المساعد الذكي بدلاً من ذلك."
NO_INPUT_FALLBACK = (
    "يمكنك التحدث معي مباشرة وسأحاول مساعدتك، أو اضغط على الشباك لسماع "
    "قائمة الأقسام مرة أخرى، أو صفر للتحدث مع أحد موظفينا."
)


def category_selected_prompt(label: str) -> str:
    return f"تفضل، اسألني عن أي شيء يخص {label}."


class AlmosaferAgent(Agent):
    def __init__(self, on_route_operator, get_active_category) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._on_route_operator = on_route_operator
        self._get_active_category = get_active_category

    @function_tool
    async def route_to_operator(self, context: RunContext) -> str:
        """استدعِ هذه الأداة عندما يطلب المتصل التحدث إلى موظف أو عملية تحويل بشرية."""
        await self._on_route_operator()
        return "تم بدء عملية التحويل."

    @function_tool
    async def search_faq(self, context: RunContext, query: str) -> str:
        """
        ابحث في الأسئلة الشائعة الخاصة بالفئة المختارة حاليًا (الطيران/الفنادق/شاليهات+/المدفوعات).
        استدعِ هذه الأداة دائمًا قبل الإجابة على أي سؤال يتعلق بسياسة أو سعر أو رسوم أو حجز.
        query: نص يلخص سؤال المتصل بكلمات مفتاحية بالعربية.
        """
        category = self._get_active_category()
        if not category:
            return (
                "لا توجد فئة مختارة حاليًا. أخبر المتصل أن عليه اختيار قسم "
                "(الطيران، الفنادق، شاليهات+، أو المدفوعات والرسوم) أولاً."
            )

        results = faq_store.search(category, query, top_n=2)
        if not results:
            return (
                "لم يتم العثور على إجابة مطابقة في الأسئلة الشائعة لهذه الفئة. "
                "اعتذر للمتصل ولا تخترع إجابة، وأخبره أنه يمكنه الضغط على صفر للتحدث مع موظف."
            )

        blocks = []
        for r in results:
            blocks.append(f"سؤال: {r['question']}\nجواب: {r['answer']}")
        return "\n\n".join(blocks)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=settings.vad_min_speech_duration,
        min_silence_duration=settings.vad_min_silence_duration,
        prefix_padding_duration=settings.vad_prefix_padding_duration,
        activation_threshold=settings.vad_activation_threshold,
    )


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    call_ended = asyncio.Event()
    participant_holder = {}
    state = {"active_category": None}
    transfer_state = {"in_progress": False}

    # One shared LiveKit API client for the whole call - avoids reconnecting
    # on every transfer attempt and every duration-limit check.
    lkapi = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model=settings.stt_model, language=settings.stt_language),
        llm=openai.LLM(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.groq_api_key,
            temperature=0.3,
        ),
        tts=elevenlabs.TTS(
            model=settings.tts_model,
            voice_id=settings.elevenlabs_voice_id,
            api_key=settings.elevenlabs_api_key,
        ),
        # Arabic isn't supported by the multilingual turn detector model
        # (confirmed by "Turn detector does not support language ar" in logs),
        # so we rely on VAD-only endpointing instead of a turn-detection model.
        turn_detection=None,
        min_endpointing_delay=settings.min_endpointing_delay,
        max_endpointing_delay=settings.max_endpointing_delay,
        preemptive_generation=True,
    )

    async def transfer_to_operator():
        if transfer_state["in_progress"]:
            # Caller pressed 0 twice in quick succession (or DTMF debounce
            # let a duplicate through) - don't fire a second transfer.
            return
        transfer_state["in_progress"] = True
        logger.info(f"Transferring caller to extension {settings.sip_transfer_extension}")
        try:
            await lkapi.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=ctx.room.name,
                    participant_identity=participant_holder["p"].identity,
                    transfer_to=settings.operator_sip_uri,
                )
            )
        except api.SipCallError as e:
            logger.error(f"Transfer failed: {e}")
            transfer_state["in_progress"] = False  # allow retry
            await session.say(TRANSFER_FAILED, allow_interruptions=True)

    async def route_operator_cb():
        await transfer_to_operator()

    def get_active_category():
        return state["active_category"]

    agent = AlmosaferAgent(
        on_route_operator=route_operator_cb,
        get_active_category=get_active_category,
    )

    # ---- DTMF handling: registered EARLY, before any speech starts ----
    last_dtmf_time = 0.0

    def on_dtmf(dtmf: rtc.SipDTMF):
        nonlocal last_dtmf_time
        loop = asyncio.get_event_loop()
        now = loop.time()
        if now - last_dtmf_time < settings.dtmf_debounce_seconds:
            return
        last_dtmf_time = now
        asyncio.create_task(handle_dtmf(dtmf.digit))

    async def handle_dtmf(digit: str):
        # "0" -> operator, works at ANY point in the call, interrupts current speech
        if digit == "0":
            await session.interrupt()
            await transfer_to_operator()
            return

        # "#" -> back to main menu, replay greeting
        if digit == "#":
            state["active_category"] = None
            await session.interrupt()
            await session.say(GREETING, allow_interruptions=True)
            return

        # "1".."4" -> select/switch category directly, even mid-conversation
        if digit in CATEGORY_LABELS:
            state["active_category"] = digit
            label = CATEGORY_LABELS[digit]
            await session.interrupt()
            await session.say(category_selected_prompt(label), allow_interruptions=True)
            return

        # anything else -> invalid key
        await session.interrupt()
        await session.say(INVALID_KEY, allow_interruptions=True)

    ctx.room.on("sip_dtmf_received", on_dtmf)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    participant = await ctx.wait_for_participant()
    participant_holder["p"] = participant

    async def enforce_max_duration():
        try:
            await asyncio.sleep(settings.max_call_duration_seconds)
            if not call_ended.is_set():
                logger.info("Max call duration reached, ending call")
                await lkapi.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
        except asyncio.CancelledError:
            pass

    duration_task = asyncio.create_task(enforce_max_duration())

    def on_disconnect(*_):
        call_ended.set()
        duration_task.cancel()
        asyncio.create_task(lkapi.aclose())

    ctx.room.on("participant_disconnected", on_disconnect)

    # Greeting is spoken AFTER the DTMF listener is live
    await session.say(GREETING, allow_interruptions=True)

    # ---- main-menu watchdog: re-prompt if no category chosen yet ----
    async def menu_watchdog():
        for _ in range(settings.menu_max_reprompts):
            await asyncio.sleep(settings.menu_timeout_seconds)
            if state["active_category"] is not None or call_ended.is_set():
                return
            await session.say(REPROMPT, allow_interruptions=True)
        if state["active_category"] is None and not call_ended.is_set():
            await session.say(NO_INPUT_FALLBACK, allow_interruptions=True)

    asyncio.create_task(menu_watchdog())


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=settings.agent_name))