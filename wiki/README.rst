# -*- mode: org; mode: visual-line; mode: org-indent; -*-

#+TITLE: FreedomBuddy: Person Focused Networking
#+DATE: <2015-02-16 Mon>
#+AUTHOR: Nick Daly
#+EMAIL: Nick.M.Daly@gmail.com
#+OPTIONS: ':nil *:t -:t ::t <:t H:3 \n:nil ^:t arch:headline
#+OPTIONS: author:t c:nil creator:comment d:(not "LOGBOOK") date:t
#+OPTIONS: e:t email:nil f:t inline:t num:t p:nil pri:nil stat:t
#+OPTIONS: tags:t tasks:t tex:t timestamp:t toc:t todo:t |:t
#+CREATOR: Emacs 24.4.1 (Org mode 8.2.10)
#+DESCRIPTION:
#+EXCLUDE_TAGS: noexport
#+KEYWORDS:
#+LANGUAGE: en
#+SELECT_TAGS: export

* Status

FreedomBuddy is *not* ready for public, in the field, deployment.  It won't fully protect your privacy, there're still a number of flaws that need to be fixed first.  Run ~grep -r FIXME *~ for details.

However, if you'd like to test and try to break the system, now is a fine time.

** Connectors

Right now, only the HTTPS connector exists.  Others are planned, including SSH.

** Encryptors

Right now, only the PGP (GnuPG) encryptor exists.  Others are planned, including SSL.

* Design

The FreedomBuddy system is simply an encrypted and authenticated remote data storage protocol.  It was originally designed to create resilient networks.  FreedomBuddy's long term goal is to allow users to exchange messages over any communication protocol, privately, using any encryption method.

Each FreedomBuddy user stores data that other users can request over the FreedomBuddy protocol.  Each user sends a request signed by their key that can only request data for that specific key:

- Me
  - Your Key ID: 3456
    - Subnode1 = "some data"
    - Subnode2 = "please reply next tuesday"
  - Other Key ID: 1123
    - SubnodeJ = "other data"

In the above example you can send me a request signed by key 3456 for Subnode1 or Subnode2.  However, you cannot request SubnodeJ, because it is accessible only to key 1123.

Each message can also include the locations to reply to, which is stored in the reserved "santiago" subnode.  When it is supplied, the list of reply locations are *replaced* with the message's list of current locations.  This makes reply location management much simpler, overall.

* Use

1. Install dependencies.  If you're on a Debian-based system, this is as simple as:

   : su -c "apt-get install python-bjsonrpc python-cheetah python-cherrypy3 python-contract python-dateutil python-gnupg python-httplib2 python-openssl python-routes python-socksipy ssl-cert"

   If you're on another system, then dependency resolution is left as an exercise for the reader.

2. Configure for first run:

   : make

* Limitations

** Attacks

** Mitigations

* Questions

* References

* License

This file is distributed under a Creative Commons Attribution-ShareAlike 3.0 Unported, Version 3 license.  This CC-By-SA license is available in both [[http://creativecommons.org/licenses/by-sa/3.0/legalcode][full]] and [[http://creativecommons.org/licenses/by-sa/3.0/][summarized]] versions from Creative Commons.  This file is also distributed under the [[http://www.gnu.org/licenses/fdl.html][GNU Free Documentation License]], version 1.3 or later.

FreedomBuddy itself is distributed under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
