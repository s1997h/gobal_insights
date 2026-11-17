"""'What If You Invented the Digital Camera... and Kodak Told You to Hide It?' - a second-person story.

A dramatised retelling of the true Kodak story, told the way the best animated "what if" stories are told:
cold open at the end, "we need to go back", the viewer as the hero, short spoken lines, dialogue, a
running gag (everything that threatens film goes into "the drawer"), a callback ("Needs work."), and a
payoff that turns the question back on the viewer.

Speakers: N narrator / Y "you" (same voice, said aloud), B Kodak bosses and executives, J Joy and the
TV news anchor. Executives other than the real quotes below are fictional composites.

Real, sourced lines and facts (see the description): the 30-second assignment ("Could we build a camera
using solid-state imagers?"); 8 pounds, 0.01 MP, 23 seconds to tape; Joy's "Needs work." and the static
face fixed within the hour; the executives' questions (TV, storage, album, when) and "15 to 20 years";
"that's cute, but don't tell anyone about it" as Sasson's later summary; 90% of US film in 1976 and ~80%
margins; Sony Mavica 1981; Barabba's report, ten years to prepare, little done; $10B sales in 1981; first
Kodak digital cameras in the 1990s at about $20,000; Ofoto 2001, 75 million users, prints; first in US
digital cameras 2005, ~$60 lost per camera; film 72% of revenue in 2000, demand under a tenth by 2010;
"for 10 minutes my kids actually thought I was cool"; Chapter 11 on 19 January 2012, 131 years old,
~1,100 patents; digital cameras dropped three weeks later; Kodak Gallery $23.8M; Instagram $1B with 13
employees; Sasson's patent expired 1995; Fujifilm +57% vs Kodak -48% (2000-2010).
"""

LINES = [
    # ------------------------------------------------------------- cold open, 2012
    ("N", "January nineteenth, twenty twelve. You're sixty-one, retired, and half asleep in front of the evening news."),
    ("J", "Breaking news tonight. Eastman Kodak, the hundred-and-thirty-one-year-old photography giant, has filed for bankruptcy."),
    ("N", "You sit up."),
    ("N", "Kodak. The company where you spent most of your working life."),
    ("N", "And the craziest part? You're not even surprised."),
    ("N", "Because thirty-seven years ago, you built the thing that killed it. And they told you to keep it quiet."),
    ("N", "To understand how, we need to go back."),
    # ------------------------------------------------------------- the assignment, 1974
    ("N", "Nineteen seventy-four. You're twenty-three, fresh out of engineering school, and you've just landed a job at Kodak."),
    ("N", "And Kodak isn't just a company. It's photography. Cameras, film, chemicals, paper. If you took a photo in America, Kodak probably got paid."),
    ("N", "One afternoon, your boss stops by your desk. The whole conversation takes about thirty seconds."),
    ("B", "Hey. Could we build a camera using solid-state imagers?"),
    ("N", "You blink."),
    ("Y", "Using what?"),
    ("B", "Those new electronic light sensors. See if you can make a picture with one."),
    ("Y", "A camera with no film? Here? At the film company?"),
    ("B", "Just see if it works."),
    ("N", "And he walks off. That's it. That's the whole assignment."),
    ("N", "So you do what any reasonable engineer would do. You raid every storeroom on the campus."),
    ("N", "A lens from a movie camera. A cassette tape recorder. A stack of circuit boards. And a lot of batteries."),
    ("N", "A year later, it's finished. It weighs eight pounds. It looks like a toaster. And it takes pictures without film."),
    # ------------------------------------------------------------- the first photo, December 1975
    ("N", "December, nineteen seventy-five. You need someone to photograph. You walk down the hall and find a lab technician named Joy."),
    ("Y", "Joy! Can I take your picture? It's for science."),
    ("N", "She shrugs and sits very still. Click."),
    ("N", "And then you wait. Twenty-three seconds. Just to save one photo onto a cassette tape."),
    ("N", "You rush back to the lab, plug the tape into a TV, and slowly, line by line, a picture appears."),
    ("N", "Her hair. A white background. And where her face should be: static."),
    ("N", "Joy leans in. She stares at the screen for a long moment."),
    ("J", "Needs work."),
    ("N", "And she walks out."),
    ("N", "But you're grinning. Because she has no idea what she just saw. The world's first digital photo."),
    ("N", "An hour later, you find the problem. A few wires the wrong way round. You fix it, and there she is. Face and all."),
    ("N", "Now you just have to show your bosses. How hard could that be?"),
    # ------------------------------------------------------------- the demo, 1976
    ("N", "Nineteen seventy-six. A windowless conference room. A long table full of very important people in very expensive suits."),
    ("N", "You don't make a speech. You just point your toaster at them. Click."),
    ("N", "You pop out the tape, slide it into the player, and their own faces show up on a TV."),
    ("N", "You're ready for questions. How does it work? How did you build it?"),
    ("N", "Instead, a man at the end of the table folds his arms."),
    ("B", "Why would anyone want to look at their pictures on a television?"),
    ("N", "Another one leans in."),
    ("B", "And where do you keep them? What does a photo album even look like?"),
    ("N", "And then, the big one."),
    ("B", "When could a customer actually buy this?"),
    ("Y", "Honestly? Fifteen, maybe twenty years."),
    ("N", "The whole room relaxes. Twenty years is forever."),
    ("N", "Years later, you'd sum up their reaction in one line. That's cute, but don't tell anyone about it."),
    # ------------------------------------------------------------- the money machine
    ("N", "After the meeting, one of the executives pulls you aside, grabs a napkin, and starts drawing."),
    ("B", "Son, let me show you how Kodak makes money. We sell you a cheap camera. Then you buy film. Then chemicals. Then paper. Then prints."),
    ("B", "Every time somebody presses that button, we get paid."),
    ("N", "And he isn't exaggerating. In nineteen seventy-six, Kodak sold ninety percent of the film in America, with profit margins of around eighty percent."),
    ("B", "And you, son, have built a camera that doesn't need film."),
    ("Y", "When you put it like that."),
    ("B", "It's a very nice toaster."),
    ("N", "So your camera goes into a drawer. Not destroyed. Not sold. Just somewhere safe, where it can't hurt anybody."),
    ("N", "And honestly? If you'd been sitting on their side of the table, you might have done exactly the same."),
    # ------------------------------------------------------------- the warning, 1981
    ("N", "For a few years, the drawer works perfectly. Then, in nineteen eighty-one, Sony shows off an electronic camera that saves photos on a floppy disk."),
    ("N", "Suddenly, Kodak's biggest customers are nervous. So Kodak's head of market research, Vince Barabba, is asked a simple question. Should we be worried?"),
    ("N", "His report comes back with bad news, and good news."),
    ("N", "The bad news: digital could replace film. The good news: it'll take about ten years. Kodak has a decade to get ready."),
    ("N", "A ten-year head start. In writing. On the desk of the people who could act on it."),
    ("N", "And over that decade, Kodak does very little to prepare. Because why would it? The film money just keeps getting bigger."),
    ("B", "Ten billion dollars in sales this year! Who needs digital?"),
    ("N", "So the report goes into the drawer too. Right next to your toaster."),
    # ------------------------------------------------------------- the long middle
    ("N", "You keep working on digital anyway. Quietly. Year after year."),
    ("N", "In the nineteen-nineties, Kodak finally sells its first digital cameras. For professionals. At around twenty thousand dollars each."),
    ("Y", "Twenty thousand?"),
    ("N", "Meanwhile, the rest of the world is catching up. Fast."),
    ("N", "In two thousand and one, Kodak goes big on digital. It even buys a photo-sharing website called Ofoto."),
    ("N", "People upload their photos and share albums with their friends. It grows to more than seventy-five million users. Years before Instagram even exists."),
    ("N", "But Kodak runs it the only way it knows how."),
    ("B", "Wonderful. Now, would you like prints?"),
    ("N", "And by two thousand five, Kodak sells more digital cameras in America than anyone else. Number one."),
    ("N", "There's just one tiny problem. A Harvard case study found Kodak was losing about sixty dollars on every digital camera it sold."),
    ("B", "Sixty dollars? Per camera?"),
    ("N", "Because a digital camera needs no film. No chemicals. No prints. The money machine has nowhere to plug in."),
    ("N", "And film is still the heart of the company. In two thousand, it brings in nearly three-quarters of Kodak's revenue. Ten years later, world demand has fallen to less than a tenth."),
    ("N", "Then phones get cameras. And suddenly, everyone on Earth has your invention in their pocket."),
    ("N", "Somewhere in there, the world finally finds out who built the first one. You. Your kids think you're cool. For about ten minutes."),
    # ------------------------------------------------------------- back to 2012
    ("N", "Which brings us back to that night in twenty twelve."),
    ("J", "Kodak says it has been unable to sell about eleven hundred digital imaging patents in time to stay afloat."),
    ("N", "Three weeks later, Kodak stops making digital cameras. Altogether."),
    ("N", "And that photo-sharing site with seventy-five million users? Kodak sells it for twenty-three point eight million dollars."),
    ("N", "The same spring, Facebook buys a photo-sharing app called Instagram, for one billion dollars. It has thirteen employees."),
    ("Y", "Thirteen?"),
    ("N", "And the patent on your camera? It ran out back in nineteen ninety-five."),
    ("N", "Here's what makes it hurt. Kodak's rival, Fujifilm, was hit by the exact same storm. Its film business collapsed too."),
    ("N", "But Fujifilm asked a different question. Not how do we save film, but what are we actually good at?"),
    ("N", "The answer was chemistry. So it moved into medical imaging, materials, and even face cream. Over the decade film died, Fujifilm's revenue grew fifty-seven percent. Kodak's fell forty-eight."),
    # ------------------------------------------------------------- the answer
    ("N", "So what really killed Kodak? Not stupidity. Not a lack of money. Not even a lack of ideas. Kodak invented the future."),
    ("N", "It just couldn't stop protecting the past. Film paid too well to let go."),
    ("N", "You lean back on the couch, and for some reason, you hear Joy's voice. Two words, from nineteen seventy-five."),
    ("J", "Needs work."),
    ("N", "She was talking about a photo. She could have been talking about Kodak."),
    ("N", "In real life, that young engineer was named Steve Sasson. He built the first digital camera at twenty-four. And Kodak put it in a drawer."),
    ("N", "So, what's in your drawer? The idea you're sitting on, because what you have right now feels too safe to risk? Tell me in the comments."),
]

VOICES = {
    "N": "iP95p4xoKVk53GoZ742B",  # Chris - Charming, Down-to-Earth (narrator and "you")
    "Y": "iP95p4xoKVk53GoZ742B",
    "B": "pqHfZKP75CvOlQylNhV4",  # Bill - Wise, Mature (boss, executives)
    "J": "EXAVITQu4vr4xnSDxMaL",  # Sarah - Confident (Joy, news anchor)
}

if __name__ == "__main__":
    import json
    import sys

    words = sum(len(t.split()) for _, t in LINES)
    chars = {}
    for s, t in LINES:
        v = VOICES[s]
        chars[v] = chars.get(v, 0) + len(t)
    print(f"{len(LINES)} lines, {words} words (~{words / 150:.1f} min), chars per voice: {chars}", file=sys.stderr)
    if len(sys.argv) > 1:
        json.dump([{"i": i, "who": s, "text": t, "voice": VOICES[s]} for i, (s, t) in enumerate(LINES)], open(sys.argv[1], "w"), indent=1)
