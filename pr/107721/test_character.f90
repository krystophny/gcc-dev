program test_character
  implicit none

  ! Test CHARACTER array constructors with type-spec
  print *, [ character(16) :: ['a','b']  ] // "|"
  print *, [[character(16) :: ['a','b'] ]] // "|"

end program test_character
