program test_character_simple
  implicit none

  ! Test CHARACTER array constructors with type-spec
  ! This should work - single brackets
  print *, [ character(16) :: ['a','b']  ] // "|"

end program test_character_simple
