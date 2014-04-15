thinkblink
==========

Making the keyboard light on thinkpads flash is pretty easy. I wanted to be able to have more than one notifiction come through.

Example:
I put four flags in the config file:
- IM (1)
- email (2)
- RSS (3)
- work-email (4)

I have some script(s) check these periodically, or have some application that can invoke a command. I tell pidgin to run `thinkblink.py IM`, my RSS client to run `thinkblink.py RSS` and so on.
Work email is really important so it will cancel RSS by running `thinkblink.py work-email; thinkblink.py -u RSS`.

Let's say I stepped away and now have IM (1), email (2) and work email (4) notifications going. My thinklight will flash "on... off on... off on off on... off... on off... on off on off..." and so on (1, 2, 4, 1, 2, 4...). This lets you see what wants your attention without anything creeping onto the screen.

If I toggle the light manually my script sees the difference and discards the top notification (4), the others (2, 1) stay set.
