# Distributed-IDM
"Download a file with the help of many devices"

It aims at distributing the work load of downloading a file among multiple machines within the same network.

Working :
  * Connection is established with the machines that respond with acceptance.
  * The information about the part of the file it has to download is sent to respective machines.
  * Each machine sends the downloaded chunk back to the master machine.
  * Finally the master merges the chunks to obtain the whole file.
