Teaching Python and Web development in the browser using MQTT

There are many web sites for an indifivual to learn MQTT and other
software technologies, but the Forest Wiki is the only free tool for
teaching MQTT, Python and Web Development in the browser. Teaching
requires an understanding of the student teacher relationship. The
teacher can supervise the student's work and decide when to publish
the solutions, or can even enforce a deadline.  The teacher can
supervise the classes' progress, and decide when to move onto the next
assignment.

Teaching in the browser eliminates the need to install software on
every student's computer. This is particularly helpful when teaching
Python.  It allows the teacher to monitor the student's work in real
time, even when they are in different rooms, buildings, or countries.
And it reducess social inequality, all that students need is a
browser, it could even be on an older computer or a tablet.

Teaching online is much harder than teaching in person. Even with Zoom
much of the necessary feedback is lost.  Often students switch off
their cameras. Online, they are slower to switch on their microphones
and respond.  In prson I had a sense of when to move onto the next
assignment.  It was easy to see how people reacted to my suggestion of
moving onto the next assignment.  All of that is lost online.

MQTT provides a gorgeous solution to this problem.  The teacher sees a
single page with all of the students listed.  He can see which
assignment they are working on.  He can hover over a student, and see
the current version of their code. He is notified when they complete
an assignment, save the page, and open the next assignment page.  And
even if the teacher closes their browser, when they open it again, the
current state of the class is downloaded automatically using retained messages.

Here is what MQTT does on the student's computers.  They are working
on an assignment in a browser page at a particular URL path.  The URL
path determines the assignment.  The MQTT path also includes the
student id.  Two seconds after they stop typing, the current version
of their code is published over MQTT.  Their work is stored as a
retained message, which only the teacher can see.  When they are done,
they save their work, and move onto the next page with the next
assignment.  Their browser leaves the page, the connection is lost,
the last will and testament deletes the old retained message and
creates a new retained message with a new path.  The teacher is
noified about both events.


With MQTT it is easy for the teacher to monitor the student's work.
In the past, without MQTT, I could only check the student's work after
it was submitted it, or I had to ask them to save it. I can keep a
particularly close eye on those students who I know are weaker.

With MQTT is is easy for the teacher to monitor the entire class's
progress.  I can see who is working on the last assignment, and who
has moved onto the next assignment.  I can figure out the right time
for the class to move onto the next assignment.

I also have my original MQTT chat application which I will to add into
this application before the conference.

While MQTT is strong in Iot, I believe it deserves a lot more users
among the web developers.  Often, Web sites are a tree of pages, MQTT
is a tree of topics.  There is a natural synergy.  For many
applications, including the Forest Wiki, it is much much easier to use
an MQTT server, than it is to build your own asynchronous server. In
fact it only took me two relaxed days to add student monitoring to the
Forest Wiki using MQTT.  No way I could have done this so fast, with
PYthon's AsyncIO or a custom Node server.


