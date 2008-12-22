bitesy:
  edit IT sample, instrument names, and song messages, en masse

-[ quick start ]---------------------------------------------------------------

top pane: currently-highlighted file, single-file editing

          can revert or commit changes to the current file.  has nothing to
          do with checkmarks.
          
          file modification date will remain unchanged.

bottom pane: checked files.  bulk editing.

             1. check some files/directories (will select recursively).
             2. type in some stuff.  use strftime if you like.
             3. hit commit.
             
             the checkmarked files will be written, and any errors will be
             indicated afterwards.  note that the modification dates of
             checkmarked files will remain unchanged, unless you set
             'preserve_file_date = False' in the source.
             
             any files that WEREN'T written (ie, error files) will remain
             checkmarked after committing, so you can go look at them.
             
             everything else will be unchecked.

-[ text encoding ]-------------------------------------------------------------

by default, all text is assumed to be in cp437.  any text you enter will be
immediately changed to cp437, and any unicode characters that can't be 
encoded will become question marks.

at some point there may be some more flexibility.  if you are using the source 
code, you can change mod_encoding (near the top of bitesy.py) to any encoding
supported by python:

        http://docs.python.org/library/codecs.html#standard-encodings 

-[ strftime ]------------------------------------------------------------------

  "do strftime" => perform strftime substitution on metadata when committing
                   ANY file (checked or top-pane).  this lets you put the date
                   and time of the file into the comments.
                   
                   for example, I like to set comments to:
                       
                       %d %B %Y
                       mrb / mrburke@gmail.com
                    
                   which will be replaced with the file date, eg:
                    
                       06 July 2002
                       mrb / mrburke@gmail.com

strftime substitution chart from http://docs.python.org/library/time.html

%a  Locale's abbreviated weekday name.	 
%A  Locale's full weekday name.	 
%b  Locale's abbreviated month name.	 
%B  Locale's full month name.	 
%c  Locale's appropriate date and time representation.	 
%d  Day of the month as a decimal number [01,31].	 
%H  Hour (24-hour clock) as a decimal number [00,23].	 
%I  Hour (12-hour clock) as a decimal number [01,12].	 
%j  Day of the year as a decimal number [001,366].	 
%m  Month as a decimal number [01,12].	 
%M  Minute as a decimal number [00,59].	 
%p  Locale's equivalent of either AM or PM.
%S  Second as a decimal number [00,61].
%U  Week number of the year (Sunday as the first day of the week) as a
    decimal number [00,53]. All days in a new year preceding the first Sunday
    are considered to be in week 0.
%w  Weekday as a decimal number [0(Sunday),6].	 
%W  Week number of the year (Monday as the first day of the week) as a
    decimal number [00,53]. All days in a new year preceding the first Monday
    are considered to be in week 0.
%x  Locale's appropriate date representation.	 
%X  Locale's appropriate time representation.	 
%y  Year without century as a decimal number [00,99].	 
%Y  Year with century as a decimal number.	 
%Z  Time zone name (no characters if no time zone exists).	 
%%  A literal '%' character.

-[ known problems ]------------------------------------------------------------

- pyIT module makes some files larger.

- the top pane doesn't get updated after a checkmarked-files commit, if the
  file displayed there was checked.  reload the file and it will be updated.

- can't edit sample/instrument 'filename' field.

-[ goodnight moon ]------------------------------------------------------------

2008 mike burke / mrb / mrburke@gmail.com
