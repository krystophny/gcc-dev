program test_char_nested
  implicit none

  ! Test 1: Single brackets - should work
  print *, "Test 1 (single brackets):"
  print *, [ character(16) :: ['a','b']  ] // "|"

  ! Test 2: Double brackets - currently fails
  print *, "Test 2 (double brackets):"
  print *, [[character(16) :: ['a','b'] ]] // "|"

end program test_char_nested
