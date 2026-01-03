---
title: "Recursive Self-Improvement"
author: Eliezer Yudkowsky
date: 2008-12-01
source_url: https://www.lesswrong.com/posts/JBadX7rwdcRFzGuju/recursive-self-improvement
---

**Followup to:** Life's Story Continues, Surprised by Brains, Cascades, Cycles, Insight, Recursion, Magic, Engelbart: Insufficiently Recursive, Total Nano Domination

I think that at some point in the development of Artificial Intelligence, we are likely to see a fast, local increase in capability - "AI go FOOM". Just to be clear on the claim, "fast" means on a timescale of weeks or hours rather than years or decades; and "FOOM" means way the hell smarter than anything else around, capable of delivering in short time periods technological advancements that would take humans decades, probably including full-scale molecular nanotechnology (that it gets by e.g. ordering custom proteins over the Internet with 72-hour turnaround time). Not, "ooh, it's a little Einstein but it doesn't have any robot hands, how cute".

Most people who object to this scenario, object to the "fast" part. Robin Hanson objected to the "local" part. I'll try to handle both, though not all in one shot today.

We are setting forth to analyze the developmental velocity of an Artificial Intelligence. We'll break down this velocity into optimization slope, optimization resources, and optimization efficiency. We'll need to understand cascades, cycles, insight and recursion; and we'll stratify our recursive levels into the metacognitive, cognitive, metaknowledge, knowledge, and object level.

## Quick review

- **Optimization slope** is the goodness and number of opportunities in the volume of solution space you're currently exploring, on whatever your problem is
- **Optimization resources** is how much computing power, sensory bandwidth, trials, etc. you have available to explore opportunities
- **Optimization efficiency** is how well you use your resources. This will be determined by the goodness of your current mind design - the point in mind design space that is your current self - along with its knowledge and metaknowledge

Optimizing *yourself* is a special case, but it's one we're about to spend a lot of time talking about.

By the time any mind solves some kind of *actual problem,* there's actually been a huge causal lattice of optimizations applied - for example, humans brain evolved, and then humans developed the idea of science, and then applied the idea of science to generate knowledge about gravity, and then you use this knowledge of gravity to finally design a damn bridge or something.

So I shall stratify this causality into levels - the boundaries being semi-arbitrary, but you've got to draw them somewhere:

- **Metacognitive** is the optimization that builds the brain - in the case of a human, natural selection; in the case of an AI, either human programmers or, after some point, the AI itself.

- **Cognitive**, in humans, is the labor performed by your neural circuitry, algorithms that consume large amounts of computing power but are mostly opaque to you. You know what you're seeing, but you don't know how the visual cortex works. The Root of All Failure in AI is to underestimate those algorithms because you can't see them... In an AI, the lines between procedural and declarative knowledge are theoretically blurred, but in practice it's often possible to distinguish cognitive algorithms and cognitive content.

- **Metaknowledge:** Discoveries about how to discover, "Science" being an archetypal example, "Math" being another. You can think of these as reflective cognitive content (knowledge about how to think).

- **Knowledge:** Knowing how gravity works.

- **Object level:** Specific actual problems like building a bridge or something.

## Sources of Non-Smoothness

I am arguing that an AI's developmental velocity will not be smooth; the following are some classes of phenomena that might lead to non-smoothness:

- **Roughness:** A search space can be naturally rough - have unevenly distributed slope. With constant optimization pressure, you could go through a long phase where improvements are easy, then hit a new volume of the search space where improvements are tough. Or vice versa.

- **Resource overhangs:** Rather than resources growing incrementally by reinvestment, there's a big bucket o' resources behind a locked door, and once you unlock the door you can walk in and take them all.

- **Cascades** are when one development leads the way to another - for example, once you discover gravity, you might find it easier to understand a coiled spring.

- **Cycles** are feedback loops where a process's output becomes its input on the next round. As the classic example of a fission chain reaction illustrates, a cycle whose underlying processes are continuous, may show qualitative changes of surface behavior - a threshold of criticality - the difference between each neutron leading to the emission of 0.9994 additional neutrons versus each neutron leading to the emission of 1.0006 additional neutrons. *k* is the effective neutron multiplication factor and I will use it metaphorically.

- **Insights** are items of knowledge that tremendously decrease the cost of solving a wide range of problems - for example, once you have the calculus insight, a whole range of physics problems become a whole lot easier to solve. Insights let you fly through, or teleport through, the solution space, rather than searching it by hand - that is, "insight" represents knowledge about the structure of the search space itself.

- **Recursion** is the sort of thing that happens when you hand the AI the object-level problem of "redesign your own cognitive algorithms".

## The Collapse of Metacognitive and Object Levels

Suppose I go to an AI programmer and say, "Please write me a program that plays chess." The programmer will tackle this using their existing knowledge and insight in the domain of chess and search trees; they will apply any metaknowledge they have about how to solve programming problems or AI problems; they will process this knowledge using the deep algorithms of their neural circuitry; and this neutral circuitry will have been designed (or rather its wiring algorithm designed) by natural selection.

If you go to a sufficiently sophisticated AI - more sophisticated than any that currently exists - and say, "write me a chess-playing program", the same thing might happen: The AI would use its knowledge, metaknowledge, and existing cognitive algorithms. Only the AI's *metacognitive* level would be, not natural selection, but the *object level* of the programmer who wrote the AI, using *their* knowledge and insight etc.

Now suppose that instead you hand the AI the problem, "Write a better algorithm than X for storing, associating to, and retrieving memories". At first glance this may appear to be just another object-level problem that the AI solves using its current knowledge, metaknowledge, and cognitive algorithms. And indeed, in one sense it should be just another object-level problem. But it so happens that the AI itself uses algorithm X to store associative memories, so if the AI can improve on this algorithm, it can rewrite its code to use the new algorithm X+1.

This means that the AI's *metacognitive* level - the optimization process responsible for structuring the AI's cognitive algorithms in the first place - has now collapsed to identity with the AI's *object* level.

For some odd reason, I run into a lot of people who vigorously deny that this phenomenon is at all novel; they say, "Oh, humanity is already self-improving, humanity is already going through a FOOM, humanity is already in a Singularity" etc. etc.

Now to me, it seems clear that - at this point in the game, in advance of the observation - it is *pragmatically* worth drawing a distinction between inventing agriculture and using that to support more professionalized inventors, versus directly rewriting your own source code in RAM. Before you can even *argue* about whether the two phenomena are likely to be similar in practice, you need to accept that they are, in fact, two different things to be argued *about.*

## The Invisible Power of Cognitive Algorithms

And I do expect them to be very distinct in practice. Inventing science is not rewriting your neural circuitry. There is a tendency to *completely overlook* the power of brain algorithms, because they are invisible to introspection. It took a long time historically for people to realize that there *was* such a thing as a cognitive algorithm that could underlie thinking. And then, once you point out that cognitive algorithms exist, there is a tendency to tremendously underestimate them, because you don't know the specific details of how your hippocampus is storing memories well or poorly - you don't know how it could be improved, or what difference a slight degradation could make. You can't draw detailed causal links between the wiring of your neural circuitry, and your performance on real-world problems. All you can *see* is the knowledge and the metaknowledge, and that's where all your causal links go; that's all that's *visibly* important.

To see the brain circuitry vary, you've got to look at a chimpanzee, basically. Which is not something that most humans spend a lot of time doing, because chimpanzees can't play our games.

You can also see the tremendous overlooked power of the brain circuitry by observing what happens when people set out to program what looks like "knowledge" into Good-Old-Fashioned AIs, semantic nets and such. Roughly, nothing happens. Well, research papers happen. But no actual intelligence happens. Without those opaque, overlooked, invisible brain algorithms, there is no real knowledge - only a tape recorder playing back human words. If you have a small amount of fake knowledge, it doesn't do anything, and if you have a huge amount of fake knowledge programmed in at huge expense, it still doesn't do anything.

So the cognitive level - in humans, the level of neural circuitry and neural algorithms - is a level of tremendous but invisible power. The difficulty of penetrating this invisibility and creating a real cognitive level is what stops modern-day humans from creating AI. (Not that an AI's cognitive level would be made of neurons or anything equivalent to neurons; it would just do cognitive labor on the same level of organization. Planes don't flap their wings, but they have to produce lift somehow.)

Recursion that can rewrite the cognitive level is *worth distinguishing*.

## What Natural Selection Teaches Us

So what happens when you start rewriting cognitive algorithms?

Well, we do have *one* well-known historical case of an optimization process writing cognitive algorithms to do further optimization; this is the case of natural selection, our alien god.

Natural selection seems to have produced a pretty smooth trajectory of more sophisticated brains over the course of hundreds of millions of years. That gives us our first data point, with these characteristics:

- Natural selection on sexual multicellular eukaryotic life can probably be treated as, to first order, an optimizer of *roughly constant efficiency and constant resources.*

- Natural selection does not have anything akin to insights. It does sometimes stumble over adaptations that prove to be surprisingly reusable outside the context for which they were adapted, but it doesn't fly through the search space like a human. Natural selection is just *searching the immediate neighborhood of its present point in the solution space, over and over and over.*

- Natural selection *does* have cascades; adaptations open up the way for further adaptations.

Anyway, what we definitely do *not* see under these conditions is *logarithmic* or *decelerating* progress. It did *not* take ten times as long to go from *H. erectus* to *H. sapiens* as from *H. habilis* to *H. erectus*. Hominid evolution did *not* take eight hundred million years of additional time, after evolution immediately produced *Australopithecus*-level brains in just a few million years after the invention of neurons themselves.

And another, similar observation: human intelligence does *not* require a hundred times as much computing power as chimpanzee intelligence. Human brains are merely three times too large, and our prefrontal cortices six times too large, for a primate with our body size.

Or again: It does not seem to require 1000 times as many genes to build a human brain as to build a chimpanzee brain, even though human brains can build toys that are a thousand times as neat.

Why is this important? Because it shows that with *constant optimization pressure* from natural selection and *no intelligent insight,* there were *no diminishing returns* to a search for better brain designs up to at least the human level. There were probably *accelerating* returns (with a low acceleration factor). There are no *visible speedbumps*, so far as I know.

## The Mathematics of Recursion

But all this is to say only of natural selection, which is not recursive.

If you have an investment whose output is not coupled to its input - say, you have a bond, and the bond pays you a certain amount of interest every year, and you spend the interest every year - then this will tend to return you a linear amount of money over time. After one year, you've received $10; after 2 years, $20; after 3 years, $30.

Now suppose you *change* the qualitative physics of the investment, by coupling the output pipe to the input pipe. Whenever you get an interest payment, you invest it in more bonds. Now your returns over time will follow the curve of compound interest, which is exponential. (Please note: *Not all accelerating processes are smoothly exponential.* But this one happens to be.)

The first process grows at a rate that is linear over *time*; the second process grows at a rate that is linear in its *cumulative return so far.*

The too-obvious mathematical idiom to describe the impact of recursion is replacing an equation

y = f(t)

with

dy/dt = f(y)

For example, in the case above, reinvesting our returns transformed the *linearly* growing y = m*t into y' = m*y whose solution is the exponentially growing y = e^(m*t).

Now... I do not think you can *really* solve equations like this to get anything like a description of a self-improving AI.

But it's the obvious reason why I *don't* expect the future to be a continuation of past trends. The future contains a feedback loop that the past does not.

As a different Eliezer Yudkowsky wrote, very long ago:

> "If computing power doubles every eighteen months, what happens when computers are doing the research?"

And this sounds horrifyingly naive to my present ears, because that's not really how it works at all - but still, it illustrates the idea of "the future contains a feedback loop that the past does not".

## Historical Trajectory

History up until this point was a long story about natural selection producing humans, and then, after humans hit a certain threshold, humans starting to rapidly produce knowledge and metaknowledge that could - among other things - feed more humans and support more of them in lives of professional specialization.

To a first approximation, natural selection held still during human cultural development. Even if Gregory Clark's crazy ideas are crazy enough to be true - i.e., some human populations evolved lower discount rates and more industrious work habits over the course of just a few hundred years from 1200 to 1800 - that's just tweaking a few relatively small parameters; it is not the same as developing new complex adaptations with lots of interdependent parts. It's not a chimp-human type gap.

So then, *with human cognition remaining more or less constant,* we found that knowledge feeds off knowledge with *k* > 1 - given a background of roughly constant cognitive algorithms at the human level. We discovered major chunks of metaknowledge, like Science and the notion of Professional Specialization, that changed the exponents of our progress; having lots more humans around, due to e.g. the object-level innovation of farming, may have have also played a role. Progress in any one area tended to be choppy, with large insights leaping forward, followed by a lot of slow incremental development.

If you were to summarize that in one breath, it would be, "with constant natural selection pushing on brains, progress was linear or mildly accelerating; with constant brains pushing on metaknowledge and knowledge and object-level progress feeding back to metaknowledge and optimization resources, progress was exponential or mildly superexponential".

## Flatline or FOOM

Now fold back the object level so that it becomes the metacognitive level.

And note that we're doing this through a chain of differential equations, not just one; it's the *final* output at the object level, after all those integrals, that becomes the velocity of metacognition.

You should get...

...very fast progress? Well, no, not necessarily. You can also get nearly *zero* progress.

If you're a recursified optimizing compiler, you rewrite yourself just once, get a single boost in speed (like 50% or something), and then never improve yourself any further, ever again.

If you're EURISKO, you manage to modify some of your metaheuristics, and the metaheuristics work noticeably better, and they even manage to make a few further modifications to themselves, but then the whole process runs out of steam and flatlines.

It was human intelligence that produced these artifacts to begin with. Their *own* optimization power is far short of human - so incredibly weak that, after they push themselves along a little, they can't push any further. Worse, their optimization at any given level is characterized by a limited number of opportunities, which once used up are gone - extremely sharp diminishing returns.

When you fold a complicated, choppy, cascade-y chain of differential equations in on itself via recursion, *it should either flatline or blow up.* You would need *exactly the right law of diminishing returns* to fly through the extremely narrow *soft takeoff keyhole.*

The *observed history of optimization to date* makes this *even more unlikely.* I don't see any reasonable way that you can have constant evolution produce human intelligence on the observed historical trajectory (linear or accelerating), and constant human intelligence produce science and technology on the observed historical trajectory (exponential or superexponential), and *fold that in on itself,* and get out something whose rate of progress is in any sense *anthropomorphic.* From our perspective it should either flatline or FOOM.

When you first build an AI, it's a baby - if it had to improve *itself,* it would almost immediately flatline. So you push it along using your own cognition, metaknowledge, and knowledge - *not* getting any benefit of recursion in doing so, just the usual human idiom of knowledge feeding upon itself and insights cascading into insights. Eventually the AI becomes sophisticated enough to start improving *itself*, not just small improvements, but improvements large enough to cascade into other improvements. (Though right now, due to lack of human insight, what happens when modern researchers push on their AGI design is mainly nothing.) And then you get what I. J. Good called an "intelligence explosion".

I even want to say that the functions and curves being such as to allow hitting the soft takeoff keyhole, is *ruled out* by observed history to date. But there are small conceivable loopholes, like "maybe all the curves change drastically and completely as soon as we get past the part we know about in order to give us exactly the right anthropomorphic final outcome", or "maybe the trajectory for insightful optimization of intelligence has a law of diminishing returns where blind evolution gets accelerating returns".

There's other factors contributing to hard takeoff, like the existence of hardware overhang in the form of the poorly defended Internet and fast serial computers. There's more than one possible species of AI we could see, given this whole analysis. I haven't yet touched on the issue of localization (though the basic issue is obvious: the initial recursive cascade of an intelligence explosion can't race through human brains because human brains are not modifiable until the AI is already superintelligent).

But today's post is already too long, so I'd best continue tomorrow.

---

**Post scriptum:** It occurred to me just after writing this that I'd been victim of a cached Kurzweil thought in speaking of the knowledge level as "exponential". Object-level resources are exponential in human history because of physical cycles of reinvestment. If you try defining knowledge as productivity per worker, I expect that's exponential too (or productivity growth would be unnoticeable by now as a component in economic progress). I wouldn't be surprised to find that published journal articles are growing exponentially. But I'm not quite sure that it makes sense to say humanity has learned as much since 1938 as in all earlier human history... though I'm quite willing to believe we produced more goods... then again we surely learned more since 1500 than in all the time before. Anyway, human knowledge being "exponential" is a more complicated issue than I made it out to be. But human object level is more clearly exponential or superexponential.
