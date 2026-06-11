# Anisodactyl

> One CRUD to rule them all.

This tries to solve the following problems:

- Nested Database Mutations - Eliminate N+1 network requests.
- URL based Sorting and Filtering - Every possible sorting and filtering available via URL.
- Pagination - Performant front-end by processing less.
- Auditing System - Keep track of who did what.
- Generic CRUD with optional Nested Structure
- Automatic CRUD endpoints

## Intro

Why write boring crud again and again especially when it's almost the same logic everywhere?

A typical CRUD manipulates a database structure in this structure where each node is a table: `Parent? --- Current --< Children?`.
Every table in your interconnected database sits at the center of it's own relationship graph; optional `Parent` pointing inwards and optional `Children` pointing outwards.

```sh
Parent=Company,Branch,School,Library,Bakery,etc.
Current=Staffs,Teachers,Employees,Trainees,Students,etc.
Children=Timetable,Appointments,Schedule,Designations,Address,Contacts,etc.
```

Current object can be anything. It can be one of the children as well, being able to create any graph like structure imaginable.

## Notes

- Package Structure: [Official Packaging Docs](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

Generate distribution archives

```sh
python3 -m pip install --upgrade build
python3 -m build
```
