import { makeStyles } from '@material-ui/core';

const useStyles = makeStyles({
  svg: { width: 'auto', height: 28 },
  mark: { fill: '#7df3e1' },
});

export const LogoIcon = () => {
  const classes = useStyles();
  return (
    <svg className={classes.svg} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 32" role="img" aria-label="platform-demo">
      <rect className={classes.mark} x="2" y="6" width="20" height="20" rx="5" />
      <rect fill="#0b1b2b" x="8" y="12" width="8" height="8" rx="2" />
    </svg>
  );
};
