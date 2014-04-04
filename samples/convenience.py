import openmetadata as om

path = r'c:\users\marcus\om2'
om.write(path, True, 'status')
om.write(path, 'There once was a boy', 'story')
om.write(path, 27, 'age')

data = {
    'firstname': 'Marcus',
    'lastname': 'Ottosson',
    'email': 'konstruktion@gmail.com'
}

for key, value in data.iteritems():
    om.write(path, value, key)

# Write deeply nested data
om.write(path, True, 'root', 'group', 'amazing')

# Successfully wrote: c:\users\marcus\om2\.meta\status.bool
# Successfully wrote: c:\users\marcus\om2\.meta\story.string
# Successfully wrote: c:\users\marcus\om2\.meta\age.int
# Successfully wrote: c:\users\marcus\om2\.meta\lastname.string
# Successfully wrote: c:\users\marcus\om2\.meta\email.string
# Successfully wrote: c:\users\marcus\om2\.meta\firstname.string
# Successfully wrote: c:\users\marcus\om2\.meta\root\group\amazing.bool
