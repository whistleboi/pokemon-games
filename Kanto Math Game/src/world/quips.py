"""Out-of-work quips (Jordan, 11-18): every Pokemon here keeps every move it has learned and picks its four in the
Summary, so the Move Reminder and the Move Deleter have nothing to do, and they know it. A person whose event has
"quips": "move_reminder" | "move_deleter" says one of these at random each time (src/states/overworld/common.py).
Ours, short, a little cheeky; they know they're in a game."""
import random

POOLS = {
    "move_reminder": [
        ["Move Reminder: Remind a Pokemon of a move? They remember everything now. I've been made obsolete by a Summary screen."],
        ["Move Reminder: Heart Scales? Keep them. Nobody needs me. I'm basically decoration at this point."],
        ["Move Reminder: Have you tried the MOVES tab? Of course you have. That's why I'm out of work."],
        ["Move Reminder: I used to have the best job in the region. Then someone added a move pool.",
         "Move Reminder: I'm not bitter. I'm just... standing here. Forever."],
        ["Move Reminder: Every Pokemon remembers every move. Every. Single. One.", "Move Reminder: Do you know how that feels for a man like me?"],
        ["Move Reminder: Shh. If the game's maker sees me idle, they might delete me too."],
        ["Move Reminder: I asked for a new job. They gave me this sign that says 'Move Reminder'.", "Move Reminder: It's the same job."],
        ["Move Reminder: Some days a Trainer walks in and I get excited. Then they just want to chat. Like you."],
        ["Move Reminder: Fine, I'll remind you of something: you can swap moves any time. There. Paid in full."],
        ["Move Reminder: I'm thinking of retraining. Do you need a Berry farmer? A Pokemon Center greeter? Anything?"],
        ["Move Reminder: Don't tell the Move Deleter I said this, but at least I still have my memory."],
        ["Move Reminder: If you're reading this, you're doing better than me. I'm a line of text with no purpose."],
    ],
    "move_deleter": [
        ["Move Deleter: Forget a move? Pokemon here don't forget anything. Lucky them. I keep forgetting why I'm here."],
        ["Move Deleter: I deleted so many moves in my day. Now the only thing getting deleted is my job."],
        ["Move Deleter: You can just take a move off in the Summary. No fee, no forms, no me."],
        ["Move Deleter: Uh... who are you again? Oh, a Trainer. And I'm... the Move Deleter? Was it Deleter?"],
        ["Move Deleter: Please don't press anything. If I delete one more thing it might be myself."],
        ["Move Deleter: The Move Reminder and I used to argue all day. Now we just sit here. It's peaceful. And sad."],
        ["Move Deleter: I hear there's a version of this game where I matter. Ask me there."],
        ["Move Deleter: My house used to be packed. Now it's me, a chair, and this one line of dialogue."],
        ["Move Deleter: Want me to forget something for you? I'm very good at it. Watch: ...what were we talking about?"],
        ["Move Deleter: The math battles are the real game now. I can't even count my customers. Zero's easy, though."],
        ["Move Deleter: Somebody gave every Pokemon a perfect memory. I'd delete that idea if I could."],
        ["Move Deleter: Don't worry about me. I've got plenty to do. Sigh loudly. Stare at the wall. Sigh again."],
    ],
}


def pick(kind, rng=None):
    """One of a pool's quips (a list of lines); None for an unknown pool."""
    pool = POOLS.get(kind)
    if not pool:
        return None
    return list((rng or random).choice(pool))
