# Anisodactyl

> One CRUD to rule them all.

Why write boring crud again and again especially when it's the same logic everywhere?

A typical CRUD manipulates a database structure in this structure where each node is a table: `Parent? --- Current --< Children?`.
Every table in your interconnected database sits at the center of it's own relationship graph; optional `Parent` pointing inwards and optional `Children` pointing outwards.

```sh
Parent=Company,Branch,School,Library,Bakery,etc.
Current=Staffs,Teachers,Employees,Trainees,Students,etc.
Children=Timetable,Appointments,Schedule,Designations,Address,Contacts,etc.
```

Current object can be anything. It can be one of the children as well, being able to create any graph like structure imaginable.
