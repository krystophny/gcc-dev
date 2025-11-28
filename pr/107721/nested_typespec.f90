! Harald's test case from Comment #18 - nested constructors losing typespec
! The issue: outer constructor without type-spec wrapping inner with type-spec
! loses the type-spec when flattened.

program nested_typespec
    implicit none
    character(17) :: r1(2), r2(2), r3(2), r4(2), r5(2)

    ! These work correctly:
    print *, '--- Working cases ---'
    print *, [character(16) :: ['a','b']]
    print *, [character(16) :: ['a','b']] // '|'

    ! These lose the typespec (the outer [] doesn't have type-spec):
    print *, '--- Failing cases ---'
    print *, [[character(16) :: ['a','b']]]          ! lost typespec
    print *, [[character(16) :: ['a','b']]] // '|'   ! lost typespec
    print *, '|' // [[character(16) :: ['a','b']]]   ! lost typespec

    ! Expected output for all:
    ! 'a               ' 'b               '
    ! 'a               |' 'b               |'
    ! 'a               ' 'b               '
    ! 'a               |' 'b               |'
    ! '|a               ' '|b               '

    ! Actual output for failing cases (wrong - not padded to 16):
    ! 'a' 'b'
    ! 'a|' 'b|'
    ! '|a' '|b'

    print *, '--- Runtime verification ---'

    ! Working cases
    r1 = [character(16) :: ['a','b']] // '|'
    if (r1(1) /= 'a               |') stop 1
    if (r1(2) /= 'b               |') stop 2
    print *, 'Test 1-2 passed: [character(16) :: [...]] // |'

    ! Failing cases - outer constructor without type-spec
    r2 = [[character(16) :: ['a','b']]] // '|'
    if (r2(1) /= 'a               |') stop 3
    if (r2(2) /= 'b               |') stop 4
    print *, 'Test 3-4 passed: [[character(16) :: [...]]] // |'

    r3 = '|' // [[character(16) :: ['a','b']]]
    if (r3(1) /= '|a               ') stop 5
    if (r3(2) /= '|b               ') stop 6
    print *, 'Test 5-6 passed: | // [[character(16) :: [...]]]'

    ! Plain nested without concat
    r4(1:2) = [[character(16) :: ['a','b']]]
    if (r4(1) /= 'a               ') stop 7
    if (r4(2) /= 'b               ') stop 8
    print *, 'Test 7-8 passed: [[character(16) :: [...]]]'

    print *, 'All tests passed!'
end program nested_typespec
